# queryX - Excel Query Assistant

![queryX Logo](static/duck.png)

## Overview

queryX (Excel Query Language) is a powerful web application that enables users to upload Excel files and query them using natural language. The tool leverages AI to generate SQL queries from plain English descriptions and executes them against your Excel data using DuckDB as the query engine.

## 🎥 Demo Video

Watch the complete walkthrough and demonstration:

> **📹 Screencast Video**: `./demo/queryx_demo.mp4`  
> *(Upload your demo video to the `demo` folder in the project root)*

## ✨ Key Features

- **Excel File Upload**: Support for multiple .xlsx files with multiple sheets
- **Smart Table Mapping**: Automatic conversion of Excel sheet names and column headers to database-safe names
- **Natural Language Queries**: Describe what you want in plain English, and AI generates the SQL
- **DuckDB Integration**: Fast, efficient querying using DuckDB engine
- **AI-Powered SQL Generation**: Uses OpenAI GPT-3.5-turbo for intelligent SQL query generation
- **Query Testing**: Test your SQL queries before downloading results
- **Multiple Export Formats**: Download results as CSV or Excel files
- **Query History**: Track all AI interactions and generated queries
- **Real-time Preview**: See query results instantly in the browser

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- OpenAI API key

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd queryX
   ```

2. **Install required packages**:
   ```bash
   pip install flask pandas duckdb openai openpyxl
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Open your browser** and navigate to:
   ```
   http://localhost:5001
   ```

## 📋 How to Use

### Step 1: Upload Excel Files
- Navigate to the home page
- Select one or more `.xlsx` files using the file picker
- Click "Upload" to process your files

### Step 2: Map Tables and Columns
- Review the automatically generated table and column names
- Modify any names if needed to make them more meaningful
- Ensure all names are database-safe (no spaces, special characters)
- Click "Save Mapping" to proceed

### Step 3: Query Your Data
1. **Enter your OpenAI API key** in the provided field
2. **Describe your query** in natural language, for example:
   - "Show me all employees in the Engineering department"
   - "What is the average salary by department?"
   - "Find employees who completed training in the last 6 months"
3. **Generate SQL**: Click "Generate SQL" to create the query
4. **Test Query**: Click "Test SQL" to preview results
5. **Download Results**: Choose CSV or Excel format and download

## 🗂️ Project Structure

```
queryX/
├── app.py                    # Main Flask application
├── README.md                 # This file
├── sample_sql_queries.md     # Example queries and data structure
├── static/                   # Static assets
│   ├── app.css              # Main stylesheet
│   ├── app_blue.css         # Alternative blue theme
│   └── duck.png             # Application logo
├── templates/               # HTML templates
│   ├── base.html            # Base template
│   ├── mapping.html         # Table/column mapping page
│   ├── rules.html           # Query interface
│   └── upload.html          # File upload page
├── test/                    # Sample test files
│   ├── departments.xlsx     # Sample department data
│   └── employees.xlsx       # Sample employee data
├── uploads/                 # User uploaded files (auto-created)
└── demo/                    # Demo videos (create this folder)
    └── queryx_demo.mp4      # Place your demo video here
```

## 🔧 Technical Details

### Core Technologies
- **Backend**: Flask (Python web framework)
- **Database Engine**: DuckDB (in-memory analytical database)
- **AI Integration**: OpenAI GPT-3.5-turbo API
- **Data Processing**: Pandas for Excel file handling
- **Frontend**: HTML, CSS, JavaScript (vanilla)

### Database Schema Handling
- Automatically converts Excel sheet names to valid table names
- Sanitizes column headers (removes spaces, special characters)
- Handles duplicate sheet names by appending numbers
- Preserves original column names for user reference

### AI Query Generation
- Uses OpenAI's GPT-3.5-turbo model
- Provides schema context to the AI for accurate SQL generation
- Tracks all AI interactions with timestamps and token usage
- Supports query refinement and testing

## 📊 Sample Data

The project includes sample Excel files in the `test/` directory:

### departments.xlsx
- **departments** sheet: department_id, department_name, budget, location, manager_name, established_date
- **projects** sheet: project_id, project_name, department_id, start_date, end_date, budget, status

### employees.xlsx
- **employees** sheet: employee_id, first_name, last_name, email, phone, department_id, position, salary, hire_date, manager_id, status
- **performance_reviews** sheet: review_id, employee_id, review_date, performance_score, goals_met, reviewer_id, comments
- **training_records** sheet: training_id, employee_id, course_name, training_date, completion_status, score, instructor, cost

## 🔍 Example Queries

Try these natural language queries with the sample data:

1. **Basic Analysis**: "Show me all employees in the Engineering department"
2. **Aggregation**: "What is the average salary by department?"
3. **Date Filtering**: "Find employees hired in the last year"
4. **Join Operations**: "Show employee performance scores with their department names"
5. **Complex Analysis**: "Which departments have the highest training completion rates?"

## ⚙️ Configuration

### Environment Variables
- Set `OPENAI_API_KEY` environment variable, or enter it in the web interface
- Modify `app.secret_key` in `app.py` for production deployment

### Customization
- Modify CSS files in `static/` to change the appearance
- Update templates in `templates/` to modify the user interface
- Adjust the AI prompt in `app.py` to change query generation behavior

## 🚀 Deployment

### Local Development
```bash
python app.py
```
Access at: http://localhost:5001

### Production Deployment
1. Set `app.run(debug=False)` in `app.py`
2. Use a production WSGI server like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5001 app:app
   ```

## 🔒 Security Considerations

- Store OpenAI API keys securely (environment variables)
- Implement proper session management for production
- Add file upload size limits and validation
- Consider user authentication for multi-user deployments

## 🐛 Troubleshooting

### Common Issues

1. **"No module named 'openpyxl'"**
   - Install with: `pip install openpyxl`

2. **OpenAI API Errors**
   - Verify your API key is valid and has sufficient credits
   - Check your internet connection

3. **DuckDB Query Errors**
   - Ensure table and column names are properly mapped
   - Check the generated SQL syntax in the query interface

4. **File Upload Issues**
   - Ensure files are in .xlsx format
   - Check file permissions and available disk space

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Submit a pull request with a clear description

## 📄 License

This project is open source. Please check the license file for details.

## 🙏 Acknowledgments

- **DuckDB**: Fast analytical database engine
- **OpenAI**: GPT-3.5-turbo for natural language processing
- **Flask**: Python web framework
- **Pandas**: Data manipulation and analysis library

---

**Note**: Remember to add your demo video to the `demo/` folder as `queryx_demo.mp4` for the screencast reference to work properly.
