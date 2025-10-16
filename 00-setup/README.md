# Setting up your environment

## Prerequisites

To run the code in this workspace, ensure you have the following tools installed:

- **Python** (latest version recommended, e.g., 3.11+)
- **[uv](https://github.com/astral-sh/uv)** (a fast Python package manager)

## Setup Instructions

1. **Install Python**

    Download and install the latest version of Python from [python.org](https://www.python.org/downloads/).

2. **Install uv**

    ```sh
    pip install uv
    ```

3. **Create a virtual environment using uv**

    ```sh
    uv venv .venv
    ```

4. **Activate the virtual environment**

    - On Windows:
      ```sh
      .venv\Scripts\activate
      ```
    - On macOS/Linux:
      ```sh
      source .venv/bin/activate
      ```

5. **Install dependencies**

    ```sh
    uv pip install -r requirements.txt
    ```

You are now ready to run the code in this workspace.