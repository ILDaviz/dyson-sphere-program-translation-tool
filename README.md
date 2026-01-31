# Dyson Sphere Program Translation Tool

An advanced, AI-powered tool for translating **Dyson Sphere Program** into Italian (or any other language).  
This tool leverages **OpenAI (GPT-4o/GPT-5)** to provide context-aware, high-quality translations that respect game UI constraints and terminology.

## 🚀 Features

*   **⚡️ High Performance**: Uses **Batch Processing** to translate thousands of lines efficiently.
*   **🎨 Beautiful UI**: Features a modern, colorful CLI interface with progress bars and rich formatting.
*   **💰 Cost Efficient**: Implements **Smart Caching**. You only pay for new lines. Re-running the tool costs **$0**.
*   **🧠 Context-Aware**: Uses the original Chinese text as a reference to disambiguate English terms (e.g., "Power" -> "Electricity" vs "Strength").
*   **🛡️ Patch-Proof**: Automatically detects if a line's meaning has changed in a game update and re-translates it.
*   **📏 UI Optimized**: Respects **Character Budgets** and original whitespace padding to ensure text fits perfectly in game UI.
*   **🚫 Anti-Hallucination**: Automatically filters AI refusals and preserves the original text if translation fails.

---

## 🎮 How to Install the Mod (Italian)

1.  Go to the game's Steam folder.
2.  Locate the `Locale` folder: `Dyson Sphere Program/DSPGAME_Data/StreamingAssets/Locale`.
3.  Create a new folder called `1040` (the standard code for Italian).
4.  Copy the contents of `translated/it/` into this `1040` folder.
5.  Edit `Header.txt` in the `Locale` directory and add this line:
    ```text
    1040,Italiano,itIT,it,2052,0
    ```
6.  Launch the game and select **Italiano** in the settings.

---

## 🛠️ For Developers

### Prerequisites
- **Python 3.12+**
- **uv** (Modern Python package manager) -> [Install uv](https://github.com/astral-sh/uv)
- An **OpenAI API Key**

### Setup

1.  **Clone and Enter**:
    ```bash
    git clone https://github.com/your-username/dyson-sphere-program-translation-tool.git
    cd dyson-sphere-program-translation-tool
    ```

2.  **Install Environment**:
    ```bash
    uv sync
    ```

3.  **Configure API Key**:
    Copy `.env.example` to `.env` and add your key:
    ```bash
    cp .env.example .env
    # Edit .env and set OPENAI_API_KEY=sk-...
    ```

### Usage

**Translate all files into Italian:**
```bash
uv run python make.py --lang it
```

**Advanced Usage:**
```bash
# Use a specific model (e.g., GPT-5 Nano)
uv run python make.py --lang it --model gpt-5-nano

# Translate a single file with custom batch size
uv run python make.py --lang it --file base.txt --batch-size 50
```

### Testing
Verify the translation logic and cache manager:
```bash
uv run python -m unittest tests/test_core.py
```

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

## ⚠️ Disclaimer

This tool is an **open-source** project. It is **not affiliated with**, **supported by**, or **approved by** **Youthcat Studio** or **Gamera Games**. All game rights belong to their respective owners.
