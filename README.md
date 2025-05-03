# Text-to-SQL Chatbot Application

A conversational AI application that converts natural language questions into SQL queries and provides visualized results.

## Watch the demo of app:

[![Watch the video](https://img.youtube.com/vi/vw_CbdgWRHM/0.jpg)](https://youtu.be/vw_CbdgWRHM)




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

1. Create and activate a virtual environment at root directory:
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
DB_USER=chatbot_user  # just a sample username , change it accordingly while creating User in ROLES 
DB_PASSWORD=testing12345 # just a sample password , change it accordingly while creating User in ROLES 
# Database Connection URLs
# PostgreSQL connection string
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}
# MySQL connection string
MYSQL_DATABASE_URL=mysql+mysqlconnector://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}
# --- Google AI Configuration ---
GOOGLE_API_KEY=YOUR_API_KEY

# --- JWT Configuration --- NOT NEEDED FOR NOW, YOU CAN CONFIGURE AND MAKE CHANGES ACCORDINGLY
# JWT_SECRET_KEY=your_secret_key
# ALGORITHM=HS256
# ACCESS_TOKEN_EXPIRE_MINUTES=30

# --- JWT Configuration (temporary values) ---
JWT_SECRET_KEY=dummy_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# --- Schema Info (Simplified - Alternative to dynamic fetching) ---
# Define tables and columns the AI should know about. Escape quotes if needed.
# Or leave empty if using dynamic schema fetching in db_service.py

DB_SCHEMA_INFO=
#DB_SCHEMA_INFO="Table: sales\nColumns: sale_id (INTEGER), product_id (INTEGER), customer_id (INTEGER), sale_date (DATE), amount (DECIMAL)\nTable: products\nColumns: product_id (INTEGER), product_name (VARCHAR), price (DECIMAL)\nTable: customers\nColumns: customer_id (INTEGER), customer_name (VARCHAR), city (VARCHAR)"

# Schema Configuration
SCHEMA_QUERY="
SELECT 
    table_name,
    string_agg(
        column_name || ' (' || data_type || ')', 
        ', ' ORDER BY ordinal_position
    ) as columns
FROM information_schema.columns 
WHERE table_schema = 'public'
GROUP BY table_name;"

DB_SCHEMA_PATH=./schema.sql
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
# RUN THIS FROM ROOT FOLDER
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
### CREATE A NEW ROLE LIKE chatbot_user with password in postgres & mysql and grant select access to Database and Tables
1. Login using the default credentials: 
   - Username: `YOUR_DB_USERNAME`
   - Password: `YOUR_DB_PASSWORD`

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
