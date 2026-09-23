# Mahindra Automotive AI Concierge — React Frontend

Modern, responsive conversational interface built with **React**, **Vite**, **TypeScript**, and **Tailwind CSS**.

## Features
- **Multi-Thread Support (Claude / ChatGPT style)**: Each chat thread has its own isolated conversation history and stage state, mapped directly to LangGraph's `thread_id` and backed by `localStorage`.
- **Dynamic Lifecycle Stage Pill**: Real-time indication of current stage (`New Lead Discovery`, `Ongoing Pipeline`, `Booked Vehicle`, `Post-Purchase Service`).
- **Inline Tool Execution Chips**: Displays status chips (`Lead Created #LEAD-XXXX`, `Service Case #CASE-XXXX Logged`) directly within assistant turns.
- **Zoho CRM Inspector Drawer**: Live slide-out panel inspecting synced records across Leads, Deals, and Cases via `/api/crm/status`.
- **Authoritative Catalog Grounding**: Markdown rendering with tables, lists, and bold highlights for zero price hallucination.

## Quick Start
```bash
# 1. Install dependencies
npm install

# 2. Start Vite development server
npm run dev
```
Open **http://localhost:3000** in your browser. All `/api` requests will automatically proxy to the FastAPI backend running on port 8000.
