""" Script translate texts """

import os
import argparse
import time
import asyncio
from dotenv import load_dotenv
from rich.console import Console
from rich.markup import escape
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn, MofNCompleteColumn, TimeElapsedColumn
from rich.panel import Panel
from src.files_map import get_files
from src.openai import translate_batch_async
from src.cache_manager import CacheManager

DEFAULT_BATCH_SIZE = 50
DEFAULT_MODEL = "gpt-5-nano"
ENCODING = 'utf-16 le'
CONCURRENT_REQUESTS = 5

console = Console()

def parse_arguments():
    parser = argparse.ArgumentParser(description='Dyson Sphere Program Translation Tool')
    parser.add_argument('--lang', type=str, required=True, help='Target language code (e.g., it, fr, es)')
    parser.add_argument('--file', type=str, help='Specific file to translate (optional)')
    parser.add_argument('--model', type=str, default=DEFAULT_MODEL, help=f'OpenAI Model to use (default: {DEFAULT_MODEL})')
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE, help='Batch size for API calls')
    return parser.parse_args()

async def process_batch_task(semaphore, batch, lang, model, cache_manager, progress, task_id, processed_lines, lines_list):
    """
    Async task to process a single batch with semaphore for concurrency control.
    """
    async with semaphore:
        batch_map = {
            str(idx): {
                "text": text, 
                "context": context,
                "len": len(text)
            } for idx, text, context in batch
        }
        
        translations = await translate_batch_async(batch_map, lang, model)
        
        # Process results
        for idx_str, translated_text in translations.items():
            original_idx = int(idx_str)
            original_item = next(((t, c) for i, t, c in batch if i == original_idx), (None, None))
            original_text, original_context = original_item
            
            if original_text:
                # Safety Check
                bad_phrases = ["cannot translate", "unable to translate", "as an ai model", "i can't"]
                if any(phrase in translated_text.lower() for phrase in bad_phrases):
                    translated_text = original_text

                cache_manager.set(original_text, translated_text, original_context)
            
            # Update line in memory for final file write
            # We access lines_list (read-only here) and modify processed_lines (thread-safe enough for list index assignment in asyncio)
            current_line = lines_list[original_idx].rstrip('\r\n')
            parts = current_line.split("\t")
            parts[3] = translated_text
            processed_lines[original_idx] = "\t".join(parts) + "\n"
            
        progress.update(task_id, advance=len(batch))
        return len(batch)

async def process_file_async(filename, lang, model, batch_size, cache_manager):
    input_path = os.path.join('original', filename)
    output_dir = os.path.join('translated', lang)
    output_path = os.path.join(output_dir, filename)

    if not os.path.exists(input_path):
        console.print(f"[yellow]⚠️  File [bold]{escape(input_path)}[/bold] not found. Skipping.[/yellow]")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    console.rule(f"[bold cyan]Processing {escape(filename)}[/bold cyan]")

    try:
        with open(input_path, "r", encoding=ENCODING) as f:
            lines = f.readlines()
    except Exception as e:
        console.print(f"[bold red]❌ Error reading {escape(input_path)}:[/bold red] {e}")
        return

    lines_to_translate = []
    processed_lines = [None] * len(lines)
    
    # Pre-process: fill known translations and identify missing ones
    for idx, line in enumerate(lines):
        clean_line = line.rstrip('\r\n')
        parts = clean_line.split("\t")
        
        if len(parts) >= 4:
            raw_text = parts[3]
            context = parts[0].strip()
            
            if raw_text.strip():
                cached_translation = cache_manager.get(raw_text, context)
                if cached_translation:
                    parts[3] = cached_translation
                    processed_lines[idx] = "\t".join(parts) + "\n"
                else:
                    lines_to_translate.append((idx, raw_text, context))
                    processed_lines[idx] = line # Placeholder (original text)
            else:
                processed_lines[idx] = line
        else:
            processed_lines[idx] = line

    if lines_to_translate:
        semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TaskProgressColumn(),
            TextColumn("ETA:"),
            TimeRemainingColumn(),
            TimeElapsedColumn(),
            console=console,
            refresh_per_second=10,
            speed_estimate_period=30.0
        ) as progress:
            task_id = progress.add_task(f"[green]Translating...[/green]", total=len(lines_to_translate))
            
            # Create batches
            tasks = []
            batches = [lines_to_translate[i:i + batch_size] for i in range(0, len(lines_to_translate), batch_size)]
            
            for batch in batches:
                task = asyncio.create_task(
                    process_batch_task(semaphore, batch, lang, model, cache_manager, progress, task_id, processed_lines, lines)
                )
                tasks.append(task)
            
            # Wait for tasks and save incrementally
            completed_count = 0
            SAVE_EVERY_N_BATCHES = 5
            
            for coro in asyncio.as_completed(tasks):
                await coro
                completed_count += 1
                
                # Incremental Save
                if completed_count % SAVE_EVERY_N_BATCHES == 0:
                    cache_manager.save()
                    
        # Final save
        cache_manager.save()
    else:
        console.print("[dim]No new lines to translate (all found in cache).[/dim]")

    # Write output file
    try:
        with open(output_path, "w", encoding=ENCODING) as f:
            f.writelines(processed_lines)
        console.print(f"[bold green]✅ Saved to[/bold green] [underline]{escape(output_path)}[/underline]")
    except Exception as e:
        console.print(f"[bold red]❌ Error writing to {escape(output_path)}:[/bold red] {e}")

async def main_async():
    load_dotenv()
    
    if not os.getenv("OPENAI_API_KEY"):
        console.print("[bold red]❌ Error: OPENAI_API_KEY not found.[/bold red]")
        console.print("Please check that your [bold].env[/bold] file exists and contains a valid key.")
        return

    args = parse_arguments()
    start_time = time.time()

    console.print(Panel.fit(
        f"[bold blue]Dyson Sphere Program Translation Tool[/bold blue]\n"
        f"Language: [bold green]{args.lang}[/bold green]\n"
        f"Model: [bold magenta]{args.model}[/bold magenta]\n"
        f"Async Batch Size: [bold yellow]{args.batch_size}[/bold yellow] | Concurrency: [bold yellow]{CONCURRENT_REQUESTS}[/bold yellow]",
        border_style="blue"
    ))
    
    files = [args.file] if args.file else get_files()
    cache_manager = CacheManager()
    
    for file in files:
        await process_file_async(file, args.lang, args.model, args.batch_size, cache_manager)

    end_time = time.time()
    elapsed = end_time - start_time
    console.rule(f"[bold green]All tasks completed in {elapsed:.2f}s![/bold green]")

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()