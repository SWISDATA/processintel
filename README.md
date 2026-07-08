![alt text](ProcessIntel.png?raw=true)

# ProcessIntel

**ProcessIntel** is an open-source application for **process mining, visualization, and interactive exploration** of process models. It enables users to import event logs, mine process models using multiple algorithms, and explore results through an **interactive graph-based interface**.

---

## Features

- **Event log & model input**
  - Import **CSV event logs**
  - Load **ProcessIntel native process models**
- **Process mining algorithms**
  - Alpha Miner
  - Heuristic Miner
  - Inductive Miner
  - Fuzzy Miner
  - Genetic Miner
- **Interactive process model visualization**
  - Fully interactive graphs
  - Click on **nodes and edges** to inspect detailed metrics and properties directly in the app
  - Filter nodes and edges using configurable metrics
- **Export capabilities**
  - Export visualizations as **SVG**, **PNG**, and **DOT** files
  - Export mined **process models** in native format
- **Flexible deployment**
  - Run locally via Streamlit
  - Can also be deployed and run as a **Nix service**

---

## Project Status

- **Current version:** `1.0.0`
- **Stability:** Ready for productive use

---

## Requirements

To run the application, the following are required:

- **Python**: 3.12 or newer
- **Graphviz**: required for process model rendering

Detailed installation instructions are available in the setup guide:

- [Python setup](SETUP.md#python-setup)
- [Graphviz setup](SETUP.md#graphviz-setup)

All Python dependencies used by the project are listed in `requirements.txt`.

---

## Running the Application

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application from the project root:

```bash
python -m streamlit run app/streamlit_app.py
```

The application will open automatically in your default web browser.

---

## Streamlit Options

This application is built using **Streamlit**, which provides a wide range of configuration options.

Streamlit behavior can be customized in several ways:

- **Configuration file** (`.streamlit/config.toml`)
- **Environment variables**
- **Command-line (CLI) arguments**
    
These options allow you to control aspects such as server settings, theming, caching behavior, and runtime performance without modifying the application code.

For a complete and up-to-date overview of all available options, please check the official [Streamlit documentation](https://docs.streamlit.io/develop/concepts/configuration/options
).

---

## Running Tests

Test dependencies are listed in:

`tests/requirements_test.txt`

Install them with:

```bash
pip install -r tests/requirements_test.txt
```
Run all tests:
```bash
python -m unittest discover -s tests -p "*_test.py"
```

---

## Nix Support

ProcessIntel supports **Nix-based environments**, enabling reproducible builds and consistent development setups.

The project can be used with Nix in multiple ways:

- **Nix development shell** for local development and experimentation
- **Nix service deployment** for running the application in a managed environment

Using Nix ensures that all dependencies (including the correct Python version and required tools) are provided automatically by the Nix environment.

For development, you can enter the Nix development shell:

```bash
nix develop --impure
```

Once inside the development shell, the project can be started normally using Python:
```bash
python -m streamlit run app/streamlit_app.py
```
The repository also contains Nix configuration files that allow the application to be deployed and run as a Nix service.

For detailed instructions on installing Nix and running the project with it, see:

[SETUP.md](SETUP.md#nix-setup)

---

## Contributing

Contributions are very welcome!
Please refer to [CONTRIBUTING.md](Contributing.md) for guidelines on reporting issues, submitting pull requests, and contributing code or documentation.

---

## License

This project is licensed under the terms described in the LICENSE file included in the repository.

---

## Feedback

If you encounter bugs or have feature requests, please open an issue on GitHub.
Your feedback helps improve ProcessIntel for everyone.