# Postman MCP Server Integration for API Design & Testing

This document provides instructions on how to configure and use the **Postman Model Context Protocol (MCP) Server** to connect AI Agents (like Claude, Cursor, Antigravity) directly to your Postman workspaces. This allows the AI to automatically look up APIs, generate mock servers, and generate source code based on API collections.

---

## 1. Postman MCP Server Overview

The Postman MCP Server provides AI with access to the world's largest API platform, enabling direct actions on workspaces, collections, environments, and mock servers.

There are 2 operation modes:
1. **Remote Server (Recommended)**: Connects via HTTP/SSE. Supports OAuth, no need to manage static API Keys (applicable for the US region).
2. **Local Server**: Runs locally via npx. Suitable for highly secure environments or internal networks. Requires a **Postman API Key**.

### Available Toolsets
Postman provides different "Profiles" based on your needs:
- **Minimal**: `https://mcp.postman.com/minimal` (Basic operations)
- **Code**: `https://mcp.postman.com/code` (Specialized for client code generation)
- **Full**: `https://mcp.postman.com/mcp` (Over 100+ Postman API tools)

---

## 2. Configuration Guide for AI Agents

Below is the integration guide for the Postman MCP Server (Local using `npx`) across 3 popular platforms: Claude Desktop, Cursor, and Antigravity.

> **Prerequisites**: 
> 1. Ensure Node.js (`npx`) is installed.
> 2. Obtain a **Postman API Key** from: [Postman API Keys](https://postman.co/settings/me/api-keys).

### 2.1 Configuration for Claude Desktop

Open the Claude Desktop configuration file:
- **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add the following configuration into the `mcpServers` block:

```json
{
  "mcpServers": {
    "postman": {
      "command": "npx",
      "args": [
        "-y",
        "@postman/mcp-server"
      ],
      "env": {
        "POSTMAN_API_KEY": "PMAK-xxxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```
*Restart Claude Desktop after saving the file.*

### 2.2 Configuration for Cursor IDE

Cursor IDE provides a visual interface to configure MCP servers.

1. Open **Cursor Settings** (Cmd + , / Ctrl + ,).
2. Navigate to **Features** > **MCP Servers**.
3. Click on **+ Add New MCP Server**.
4. Fill in the following details:
   - **Type**: `command`
   - **Name**: `postman`
   - **Command**: `npx -y @postman/mcp-server`
5. Click the "Settings" (gear) icon next to the newly created server, and add an Environment Variable:
   - Key: `POSTMAN_API_KEY`
   - Value: `PMAK-xxxxxxxxxxxxxxxxxxxxx`

### 2.3 Configuration for Google Antigravity

In Antigravity, MCP Server configurations are defined in the `mcp_config.json` file located in the workspace `.agents/` directory or the global config directory `~/.gemini/config/`.

Create/edit the `mcp_config.json` file:

```json
{
  "mcpServers": {
    "postman-api": {
      "command": "npx",
      "args": [
        "-y",
        "@postman/mcp-server"
      ],
      "env": {
        "POSTMAN_API_KEY": "PMAK-xxxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

---

## 3. Typical Use Cases (Example Prompts)

Once successfully connected, you can ask the AI to perform the following tasks:

### API Specification Extraction & Synchronization
> *"Using Postman MCP, get me the list of endpoints from the 'E-commerce API' workspace. Based on that, generate an OpenAPI 3.1 contract file adhering to the project's standards."*

### Automated Mock Server Creation for Frontend
> *"I have just written the OpenAPI contract for the Order Service. Use Postman MCP to create a new collection and initialize a Mock Server so the Frontend team can start calling the API immediately."*

### Client Code Generation
> *"Read the structure of the `POST /orders` endpoint in the project's Postman collection. Generate Axios (TypeScript) code to call this API, including the interfaces for the request and response."*

### API Testing
> *"Write test scripts in Postman (using JavaScript/Chai) for the `GET /orders` endpoint to verify: (1) Status code is 200, (2) Response contains pagination data, (3) Response time is under 500ms."*
