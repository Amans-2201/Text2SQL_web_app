# text2sql-app Documentation

## 1. Overview

The **text2sql-app** is a web application that enables users to query a database using natural language. Users input questions in a chat interface, and the app translates these into SQL queries, executes them, and displays the results along with summaries or visualizations.

## 2. High-Level Architecture

The application follows a client-server model:

```plaintext
+-----------------+      +------------------------+      +-----------------+
|  User Browser   |      |      Backend Server    |      |   User's SQL    |
| (React Frontend)|<----->| (API, Text-to-SQL,   |<----->|    Database     |
| - Chat UI       | HTTP |  DB Interaction, Auth)|      | (e.g., Postgres)|
| - Results       |      |                        |      |                 |
| - Visualization |      +------------------------+      +-----------------+
+-----------------+
```

### Components:
- **Frontend (Client-Side)**: React-based SPA providing UI and interacting with the backend via API.
- **Backend (Server-Side)**: API server handling user requests, text-to-SQL translation, DB interaction, and auth.
- **Database**: SQL database queried by the backend.

## 3. Frontend Architecture (React SPA)

### Frameworks & Styling:
- **React**, **Tailwind CSS**

### Core Components:
- `ChatInterface.js`: Manages chat state, handles API calls, local storage.
- `MessageList.js`: Displays chat messages, uses `react-window` and `react-virtualized-auto-sizer` for performance.
- `MessageBubble.js`: Styles messages by sender (user/bot).
- `ChatInput.js`: Input field with send/cancel logic, Enter key support.
- `ResultsDisplay.js` *(inferred)*: Displays SQL results and visualizations.
- `DatabaseInfo.js` *(inferred)*: Shows schema info in a sidebar.
- `ThemeToggle.js` *(inferred)*: Switches between light and dark modes.
- `ErrorBoundary.js`: Catches render errors, prevents full app crash.

### State Management:
- React Hooks (`useState`, `useEffect`, `useRef`, `useCallback`)
- `useAuth` hook (likely Context API)
- `LocalStorage`: Stores chat history, last result
- `lodash.debounce`: Optimizes local storage writes

### API Communication:
- `apiClient` (likely Axios): Handles requests, loading states, request cancellation via `AbortController`

### Features:
- Chat UI
- Display results (including visualizations)
- Loading states and cancelable requests
- Chat history persistence
- Query suggestions
- Theme switching
- Performance optimizations (memoization, virtualization, debouncing)

## 4. Backend Architecture (Inferred)

### Language/Framework:
- Likely **Python** (Flask/FastAPI/Django) or **Node.js** (Express)

### Core Logic:

#### Text-to-SQL Engine:
- Uses NLP/ML (e.g., fine-tuned T5/BART models)
- Schema-aware (via config or dynamic retrieval)

#### Database Interaction:
- Drivers (e.g., `psycopg2`, `mysql.connector`) or ORMs (e.g., `SQLAlchemy`, `Prisma`)
- Parameterized queries to prevent SQL injection

#### Result Processing:
- Formats data for frontend (e.g., columns + rows)
- May include natural language summaries

#### Visualization Support:
- Generates chart configs (e.g., Vega-Lite, Plotly)

#### Suggestion Engine:
- Suggests sample queries based on schema or patterns

#### Authentication/Authorization:
- Likely uses JWT tokens for auth

### API Endpoints (examples):
- `POST /chat/ask`: Process a user question → SQL → results
- `GET /chat/suggestions`: Returns suggested queries
- `POST /visualization`: Converts data into a chart config
- `POST /auth/login`, `POST /auth/logout`: Auth endpoints
- `GET /database/schema`: Returns DB schema info

## 5. Database

### Type:
- Relational (PostgreSQL, MySQL, SQLite, SQL Server)

### Role:
- Stores user-queryable data
- Backend generates and executes SQL queries against it

## 6. Data Flow (Example)

### Example Question: *"Show me the total sales per region"*

1. **User Input**: Entered via `ChatInput` → Submit
2. **Frontend Request**:
    - `ChatInterface` updates state, sends:
    ```http
    POST /chat/ask
    {
      "question": "Show me the total sales per region"
    }
    ```
    - Includes JWT auth token

3. **Backend Processing**:
    - Auth token verified
    - Question passed to Text-to-SQL engine
    - Schema-aware engine generates SQL:
      ```sql
      SELECT region, SUM(amount) FROM sales GROUP BY region;
      ```
    - SQL executed against connected database

4. **Database Execution**:
    ```json
    [
      { "region": "North", "total_sales": 5000 },
      { "region": "South", "total_sales": 7500 }
    ]
    ```

5. **Backend Response**:
    ```json
    {
      "summary": "Here's the total sales per region:",
      "columns": ["region", "total_sales"],
      "data": [
        ["North", 5000],
        ["South", 7500]
      ]
    }
    ```

6. **Frontend Update**:
    - `ChatInterface` stops loading
    - Displays result summary in chat
    - `ResultsDisplay` renders data table/chart

## 7. Key Technologies Summary

### Frontend:
- React, Tailwind CSS, JavaScript, HTML, CSS
- `react-window`, Axios, Lodash (debounce)

### Backend:
- Python (Flask/FastAPI) or Node.js (Express)
- Text-to-SQL Model/Library
- SQL Driver or ORM
- JWT (auth)

### Database:
- Relational SQL (PostgreSQL, MySQL, etc.)

### Communication:
- RESTful API over HTTP/S

## 8. Design Considerations & Trade-offs

- **SPA Choice**: React offers interactivity and flexibility
- **Performance**: Uses memoization, virtualization, debouncing
- **State Management**: Local state via hooks sufficient; may scale to Redux/Zustand
- **Text-to-SQL Accuracy**: Most critical component
- **Security**: Must use parameterized queries, solid auth
- **Schema Awareness**: Essential for accurate query generation
- **Cancellation Support**: Improves UX for long queries

---

This document provides a comprehensive architectural overview of the text2sql-app, detailing its components, technologies, and data flow.