""" Script translate texts """

import os
import argparse
import time
from dotenv import load_dotenv
from rich.console import Console
from rich.markup import escape
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn, MofNCompleteColumn
from rich.panel import Panel
from src.files_map import get_files
from src.openai import translate_batch
from src.cache_manager import CacheManager

DEFAULT_BATCH_SIZE = 20
DEFAULT_MODEL = "gpt-5-nano"
ENCODING = 'utf-16 le'

console = Console()

def parse_arguments():
    parser = argparse.ArgumentParser(description='Dyson Sphere Program Translation Tool')
    parser.add_argument('--lang', type=str, required=True, help='Target language code (e.g., it, fr, es)')
    parser.add_argument('--file', type=str, help='Specific file to translate (optional)')
    parser.add_argument('--model', type=str, default=DEFAULT_MODEL, help=f'OpenAI Model to use (default: {DEFAULT_MODEL})')
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE, help='Batch size for API calls')
    return parser.parse_args()

def process_file(filename, lang, model, batch_size, cache_manager):
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
                    processed_lines[idx] = line # Placeholder
            else:
                processed_lines[idx] = line
        else:
            processed_lines[idx] = line

    if lines_to_translate:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TaskProgressColumn(),
            TextColumn("ETA:"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"[green]Translating...[/green]", total=len(lines_to_translate))
            
            for i in range(0, len(lines_to_translate), batch_size):
                batch = lines_to_translate[i:i + batch_size]
                batch_map = {
                    str(idx): {
                        "text": text, 
                        "context": context,
                        "len": len(text)
                    } for idx, text, context in batch
                }
                
                translations = translate_batch(batch_map, lang, model)
                
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
                    
                    # Update line
                    current_line = lines[original_idx].rstrip('\r\n')
                    parts = current_line.split("\t")
                    parts[3] = translated_text
                    processed_lines[original_idx] = "\t".join(parts) + "\n"
                
                progress.update(task, advance=len(batch))
                
        cache_manager.save()
    else:
        console.print("[dim]No new lines to translate (all found in cache).[/dim]")

    try:
        with open(output_path, "w", encoding=ENCODING) as f:
            f.writelines(processed_lines)
        console.print(f"[bold green]✅ Saved to[/bold green] [underline]{escape(output_path)}[/underline]")
    except Exception as e:
        console.print(f"[bold red]❌ Error writing to {escape(output_path)}:[/bold red] {e}")

def main():
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
        f"Model: [bold magenta]{args.model}[/bold magenta]",
        border_style="blue"
    ))
    
    files = [args.file] if args.file else get_files()
    cache_manager = CacheManager()
    
    for file in files:
        process_file(file, args.lang, args.model, args.batch_size, cache_manager)

    end_time = time.time()
    elapsed = end_time - start_time
    console.rule(f"[bold green]All tasks completed in {elapsed:.2f}s![/bold green]")

if __name__ == "__main__":
    main()
