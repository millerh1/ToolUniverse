Claude Desktop Setup
====================

**Connect ToolUniverse to Claude Desktop App**

Claude Desktop provides a user-friendly interface for scientific research with ToolUniverse's 1000+ tools through the Model Context Protocol (MCP).

.. seealso:: `Claude Desktop MCP official guide <https://modelcontextprotocol.io/docs/develop/connect-local-servers>`_

Setup Steps
-----------

.. card:: Step 1: Install uv
   :class-card: step-card current

   ``uv`` is the package manager that runs ToolUniverse. Install it with one command:

   .. tab-set::

      .. tab-item:: macOS (recommended)

         .. code-block:: bash

            brew install uv

         If you don't have Homebrew: `brew.sh <https://brew.sh>`_ — or use the installer below.

      .. tab-item:: macOS / Linux (installer)

         .. code-block:: bash

            curl -LsSf https://astral.sh/uv/install.sh | sh

         Then close and reopen your terminal.

      .. tab-item:: Windows

         .. code-block:: powershell

            powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

         Then close and reopen PowerShell.

   Verify it works: run ``uvx --version`` in your terminal. You should see a version number.

.. card:: Step 2: Add ToolUniverse to Claude Desktop
   :class-card: step-card

   1. Open **Claude Desktop** → **Settings** → **Developer** → **Edit Config**
   2. Your text editor opens ``claude_desktop_config.json``
   3. Replace the file contents with:

   .. code-block:: json

      {
        "mcpServers": {
          "tooluniverse": {
            "command": "uvx",
            "args": ["tooluniverse"],
            "env": {"PYTHONIOENCODING": "utf-8"}
          }
        }
      }

   4. Save the file.

   .. note::

      If you already have other MCP servers in the file, add the ``"tooluniverse": {...}`` block
      inside your existing ``"mcpServers"`` object — don't replace the whole file.

.. card:: Step 3: Restart & Verify
   :class-card: step-card pending

   1. **Fully quit** Claude Desktop — use **Quit** from the menu bar (⌘Q on Mac), not just close the window.
   2. Reopen Claude Desktop.
   3. Look for a 🔨 **hammer icon** at the bottom of the chat input box.
      Click it — you should see ``tooluniverse`` listed.
   4. Try asking: *"What scientific tools are available?"*

   .. success:: ✅ If ToolUniverse tools appear, you're all set!

.. card:: Step 4: Install Agent Skills (optional but recommended)
   :class-card: step-card pending

   Skills are pre-built research workflows that guide Claude through complex tasks:

   .. code-block:: bash

      npx skills add mims-harvard/ToolUniverse

   .. dropdown:: 💡 What are Agent Skills?
      :animate: fade-in-slide-down
      :color: primary

      Skills teach Claude how to use ToolUniverse's 1200+ tools effectively. Examples:

      - **"Research the drug metformin"** → full drug profile with safety data
      - **"Find protein structures for EGFR"** → retrieves and assesses PDB entries
      - **"What does the literature say about CRISPR?"** → deep literature review

Example Queries
---------------

.. tab-set::

   .. tab-item:: Drug Research

      .. code-block:: text

         "Find information about aspirin, including its safety profile
         and adverse events from FDA databases"

   .. tab-item:: Protein Analysis

      .. code-block:: text

         "Get comprehensive information about protein P05067,
         including its function, structure, and interactions"

   .. tab-item:: Disease Targets

      .. code-block:: text

         "Find therapeutic targets for Alzheimer's disease
         and rank them by evidence strength"

   .. tab-item:: Literature Search

      .. code-block:: text

         "Search for recent publications about mRNA vaccines
         and summarize key findings"

Troubleshooting
---------------

.. dropdown:: ❌ Hammer icon missing / "Failed to spawn" / "ENOENT" error
   :animate: fade-in-slide-down
   :color: danger

   **Cause:** Claude Desktop is a GUI app — it can't find ``uvx`` if it's in ``~/.local/bin``
   (the default location for the shell installer).

   **Fix:** Find your full ``uvx`` path and use it in the config:

   .. code-block:: bash

      which uvx    # macOS / Linux — e.g. /opt/homebrew/bin/uvx or /Users/you/.local/bin/uvx

   .. code-block:: powershell

      where uvx    # Windows

   Then update the ``"command"`` in your config to that full path:

   .. code-block:: json

      {
        "mcpServers": {
          "tooluniverse": {
            "command": "/opt/homebrew/bin/uvx",
            "args": ["tooluniverse"],
            "env": {"PYTHONIOENCODING": "utf-8"}
          }
        }
      }

   Fully quit and reopen Claude Desktop.

   .. tip:: If you installed via **Homebrew** (``brew install uv``), this error won't occur —
      Homebrew places ``uvx`` in a system path Claude Desktop can always find.

   **Check the logs** for the exact error message:

   .. code-block:: bash

      tail -f ~/Library/Logs/Claude/mcp*.log          # macOS

   .. code-block:: powershell

      type "$env:APPDATA\Claude\logs\mcp*.log"         # Windows

.. dropdown:: ❌ Tools not working after config is correct
   :animate: fade-in-slide-down
   :color: danger

   1. Make sure you **fully quit** Claude Desktop (⌘Q / right-click Dock → Quit), not just closed the window.
   2. Check JSON syntax — no trailing commas. Validate at `jsonlint.com <https://jsonlint.com>`_.
   3. Run ``uvx tooluniverse --help`` in your terminal to confirm the package works.
   4. Check logs: ``tail -20 ~/Library/Logs/Claude/mcp*.log``

.. dropdown:: ⚠️ "Too many tools" or context limit errors
   :animate: fade-in-slide-down
   :color: warning

   Add ``"--compact-mode"`` to the args:

   .. code-block:: json

      {
        "mcpServers": {
          "tooluniverse": {
            "command": "uvx",
            "args": ["tooluniverse", "--compact-mode"],
            "env": {"PYTHONIOENCODING": "utf-8"}
          }
        }
      }

.. dropdown:: 🔑 Adding API keys for more tools
   :animate: fade-in-slide-down
   :color: info

   Add keys to the ``"env"`` block in your config:

   .. code-block:: json

      {
        "mcpServers": {
          "tooluniverse": {
            "command": "uvx",
            "args": ["tooluniverse"],
            "env": {
              "PYTHONIOENCODING": "utf-8",
              "NCBI_API_KEY": "your_key_here",
              "SEMANTIC_SCHOLAR_API_KEY": "your_key_here"
            }
          }
        }
      }

   See :doc:`../api_keys` for all available keys (all are free to obtain).

Next Steps
----------

.. grid:: 1 1 2 2
   :gutter: 3

   .. grid-item-card:: 📚 Learn Tool Discovery
      :link: ../finding_tools
      :link-type: doc
      :class-card: hover-lift
      :shadow: md
      
      How to find the right tools for your research

   .. grid-item-card:: 🎯 Case Study
      :link: ../tooluniverse_case_study
      :link-type: doc
      :class-card: hover-lift
      :shadow: md
      
      End-to-end drug discovery example

.. button-ref:: index
   :color: secondary
   :shadow:
   :expand:

   ← **Back to Platform Selector**

Need Help?
----------

- 💬 **Community**: `Join our Slack <https://join.slack.com/t/tooluniversehq/shared_invite/zt-3dic3eoio-5xxoJch7TLNibNQn5_AREQ>`_
- 🐛 **Issues**: `GitHub Issues <https://github.com/mims-harvard/ToolUniverse/issues>`_
- 📖 **Documentation**: :doc:`../../index`
