# 💻 DocSense Frontend

The modern user interface for the **DocSense** hybrid-search & verified RAG document Q&A platform, built with React 19, Vite, Tailwind CSS, and Clerk Authentication.

---

## 🛠️ Tech Stack

- **Framework**: React 19 + Vite (TypeScript)
- **Styling**: Tailwind CSS
- **Authentication**: Clerk React SDK
- **Icons**: Lucide React
- **Markdown & Code Rendering**: React Markdown

---

## 🚀 Getting Started

### 1. Install Dependencies
```bash
npm install
```

### 2. Environment Variables
Create a `.env.local` file:
```env
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
```

### 3. Run Development Server
```bash
npm run dev
```

The app will be available at `http://localhost:3000` and automatically proxies API requests (`/api`) to the backend at `http://localhost:8000`.

---

## 📦 Build for Production
```bash
npm run build
```
