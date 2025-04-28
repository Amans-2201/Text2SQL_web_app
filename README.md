# Text-to-SQL Chatbot Application

A conversational AI application that converts natural language questions into SQL queries and provides visualized results.

## Features

- **Natural Language to SQL:** Convert user questions into SQL queries using Google's Gemini AI
- **Interactive Chat Interface:** User-friendly chat interface for data queries
- **Data Visualization:** Automatic chart suggestions based on query results
- **Authentication:** JWT-based user authentication
- **Real-time Schema Understanding:** Dynamic database schema fetching for accurate query generation

## Tech Stack

### Backend
- FastAPI (Python web framework)
- PostgreSQL (Database)
- Google Gemini AI (Natural Language Processing)
- JWT Authentication
- SQLParse (SQL validation)

### Frontend
- React.js
- Tailwind CSS
- Axios (API client)
- Recharts (Data visualization)
- React Router (Navigation)

## Prerequisites

- Python 3.8+
- Node.js 14+
- PostgreSQL 12+
- Google AI API Key

## Installation

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Unix/MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=Sales_DB
DB_USER=your_user
DB_PASSWORD=your_password
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}
GOOGLE_API_KEY=your_google_api_key
JWT_SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env` file:
```env
REACT_APP_API_URL=http://localhost:8000/api/v1
```

## Running the Application

### Start the Backend Server

```bash
cd backend
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### Start the Frontend Development Server

```bash
cd frontend
npm start
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Usage

1. Login using the default credentials:
   - Username: `testuser`
   - Password: `password`

2. Ask questions about your data in natural language:
   - "Show me all sales"
   - "How many customers do we have?"
   - "What is the total revenue?"

3. View results in table or chart format

## API Endpoints

- `POST /api/v1/auth/login` - User authentication
- `POST /api/v1/chat/ask` - Process natural language queries

## Development

### Project Structure
```
text2sql-app/
├── backend/
│   ├── api/
│   ├── core/
│   ├── schemas/
│   ├── services/
│   └── main.py
└── frontend/
    ├── public/
    └── src/
        ├── components/
        ├── contexts/
        ├── services/
        └── App.js
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Gemini AI for natural language processing
- FastAPI for the robust backend framework
- React.js for the frontend interface
