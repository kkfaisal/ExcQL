from flask import Flask, render_template, render_template_string, request, redirect, url_for, session, send_file, make_response
import pandas as pd
from io import BytesIO
import os
import re
from datetime import datetime
import tempfile
import openai
import duckdb

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Add a global style for all templates
base_style = ''

upload_template = '''
<link rel="stylesheet" href="/static/app.css">
<style>
.queryx-header {
    width: 100vw;
    position: fixed;
    top: 0;
    left: 0;
    z-index: 2000;
    background: #fff;
    border-bottom: 1px solid #b3d1f7;
    box-shadow: 0 2px 8px rgba(33,118,174,0.04);
    padding: 12px 0 8px 0;
}
.queryx-logo {
    font-size: 2.2em;
    font-weight: 700;
    letter-spacing: 1px;
    text-align: center;
}
.queryx-logo .x {
    color: #2176ae;
    font-size: 1.2em;
    font-family: 'Courier New', Courier, monospace;
    text-shadow: 0 2px 8px #b3d1f7;
}
.main-content {
    margin-top: 60px;
}
</style>
<div class="queryx-header">
    <div class="queryx-logo">query<span class="x">X</span></div>
</div>
<div class="main-content">
<div class="centered-container">
<h2>Upload Excel Files</h2>
<form method="post" enctype="multipart/form-data">
        <input type="file" name="files" multiple required accept=".xlsx"><br><br>
        <input type="submit" value="Upload" class="btn-main">
</form>
</div>
</div>
'''

mapping_template = '''
<link rel="stylesheet" href="/static/app.css">
<div class="centered-container">
<h2 style="text-align:center;">Table and Column Mapping</h2>
<form method="post">
    {% for file, sheets in excel_data.items() %}
        <div class="sheet-block">
        <h3>{{ file }}</h3>
        {% for sheet, sheetdata in sheets.items() %}
            <b>Sheet: {{ sheet }}</b><br>
            <div class="table-name-input">
                Table name: <input name="table_{{ file }}_{{ sheet }}" value="{{ sheetdata.safe_sheet }}" required>
            </div>
            <table class="columns-table">
                <tr><th>Original Name</th><th>Final Name (DB Safe)</th></tr>
                {% for col in sheetdata.columns %}
                <tr>
                    <td>{{ col.original }}</td>
                    <td>
                        <input name="col_{{ file }}_{{ sheet }}_{{ loop.index0 }}" value="{{ col.safe }}" required>
                    </td>
                </tr>
                {% endfor %}
            </table>
            <br>
        {% endfor %}
        </div>
    {% endfor %}
    <div style="text-align:center;">
        <input type="submit" value="Save Mapping" class="btn-main">
    </div>
</form>
</div>
'''

@app.route('/', methods=['GET', 'POST'])
def upload():
	if request.method == 'POST':
		print("POST request received")  # Debug logging
		files = request.files.getlist('files')
		print(f"Files received: {len(files) if files else 0}")  # Debug logging
		
		if not files:
			print("No files in request")
			return render_template('upload.html')
		
		filepaths = []
		for f in files:
			if f and f.filename and f.filename != '':  # Make sure file is valid
				print(f"Processing file: {f.filename}")
				path = os.path.join(UPLOAD_FOLDER, f.filename)
				f.save(path)
				filepaths.append(path)
		
		print(f"Valid files processed: {len(filepaths)}")
		
		if len(filepaths) == 0:
			print("No valid files found")
			return render_template('upload.html')
			
		session['filepaths'] = filepaths
		print("Redirecting to mapping page")
		return redirect(url_for('mapping'))
	
	print("GET request - showing upload page")
	return render_template('upload.html')

@app.route('/mapping', methods=['GET', 'POST'])
def mapping():
    filepaths = session.get('filepaths', [])
    excel_data = get_excel_data(filepaths)
    
    if request.method == 'POST':
        mapping = {}
        # Use full file path for mapping keys
        for file_path, sheets in excel_data.items():
            for sheet, sheetdata in sheets.items():
                table = request.form.get(f'table_{file_path}_{sheet}')
                renamed_cols = []
                for idx, col in enumerate(sheetdata['columns']):
                    col_val = request.form.get(f'col_{file_path}_{sheet}_{idx}')
                    renamed_cols.append({'original': col['original'], 'safe': col_val.strip()})
                key = f"{file_path}::{sheet}"
                mapping[key] = {'table': table, 'columns': renamed_cols}
        session['mapping'] = mapping
        return redirect(url_for('rules'))
    return render_template('mapping.html', excel_data=excel_data)

@app.route('/rules', methods=['GET', 'POST'])
def rules():
    sql = None
    test_result = None
    test_error = None
    prompt = ''
    error = ''
    api_key = ''
    
    # Initialize LLM prompts in session if not exists
    if 'llm_prompts' not in session:
        session['llm_prompts'] = []
    
    # Check for download errors from previous attempts
    download_error = session.pop('download_error', None)
    if download_error:
        error = download_error
    filepaths = session.get('filepaths', [])
    mapping = session.get('mapping', None)
    file_path_map = {os.path.basename(fp): fp for fp in filepaths}
    duckdb_tables = []
    duckdb_columns = {}
    con = duckdb.connect()
    try:
        if mapping:
            # Use mapped table and column names
            for key, mapinfo in mapping.items():
                table_name = re.sub(r'[^a-zA-Z0-9_]', '', mapinfo['table'].replace(' ', '_').replace('-', '_')).lower()
                filename, sheet = key.split('::')
                file_path = file_path_map[filename]
                xls = pd.ExcelFile(file_path)
                df = xls.parse(sheet)
                # Rename columns according to mapping
                col_map = {col['original']: col['safe'] for col in mapinfo['columns']}
                df = df.rename(columns=col_map)
                con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")
                duckdb_tables.append(table_name)
                # Store both original and sanitized column names as pairs
                column_pairs = []
                for col in mapinfo['columns']:
                    column_pairs.append({'original': col['original'], 'sanitized': col['safe']})
                duckdb_columns[table_name] = column_pairs
        else:
            # Fallback to original sheet/column names
            for path in filepaths:
                xls = pd.ExcelFile(path)
                for sheet in xls.sheet_names:
                    df = xls.parse(sheet)
                    safe_sheet = re.sub(r'[^a-zA-Z0-9_]', '', sheet.replace(' ', '_').replace('-', '_')).lower()
                    con.execute(f"CREATE TABLE {safe_sheet} AS SELECT * FROM df")
                    duckdb_tables.append(safe_sheet)
                    # Store both original and sanitized column names as pairs
                    column_pairs = []
                    for col in df.columns:
                        safe_col = re.sub(r'[^a-zA-Z0-9_]', '', str(col).replace(' ', '_').replace('-', '_')).lower()
                        column_pairs.append({'original': col, 'sanitized': safe_col})
                    duckdb_columns[safe_sheet] = column_pairs
        schema = []
        for tname in duckdb_tables:
            col_strs = []
            for col_pair in duckdb_columns[tname]:
                col_strs.append(f"{col_pair['sanitized']}")
            schema.append(f"Table: {tname}\n  Columns: " + ', '.join(col_strs))
        schema_str = '\n'.join(schema)
    except Exception as e:
        error = f"Error loading Excel files: {e}"
        duckdb_columns = {}
        schema_str = ''

    rule_text = ''
    if request.method == 'POST':
        try:
            action = request.form.get('action', '')
            tab_source = request.form.get('tab_source', '')
            sql = request.form.get('sql', None)
            test_error = request.form.get('test_error', None)
            rule_text = request.form.get('rule_text', '')
            
            # Track tab context in session
            session['last_action'] = action
            if tab_source:
                session['tab_source'] = tab_source
            
            # Special handling for write action - no OpenAI needed
            if action == 'write':
                try:
                    if sql:
                        sql_clean = re.sub(r'^```[a-zA-Z]*\s*', '', sql.strip())
                        sql_clean = re.sub(r'```$', '', sql_clean.strip())
                        result = con.execute(sql_clean).fetchdf()
                        test_result = result.to_string()
                        test_error = ''  # Clear error after successful run
                except Exception as e:
                    test_error = str(e)
            else:
                # For all other actions that require OpenAI
                api_key = request.form.get('api_key', '')
                if not api_key:
                    error = 'Please enter your OpenAI API key.'
                else:
                    openai.api_key = api_key
                prompt = f"""
You are an expert SQL developer. The target database is DuckDB (https://duckdb.org/), which is similar to PostgreSQL/SQLite but has its own quirks.

Given the following table schema (actual loaded tables and columns):
{schema_str}

And the following rule description:
{rule_text}

Write a valid DuckDB SQL query for this rule. Output only the SQL code, nothing else.
"""
                if action == 'generate':
                    try:
                        response = openai.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are a helpful assistant that writes SQL queries for DuckDB."},
                                {"role": "user", "content": prompt}
                            ],
                            max_tokens=512,
                            temperature=0.1
                        )
                        sql_raw = response.choices[0].message.content.strip()
                        # Remove markdown code block markers from LLM output
                        sql = re.sub(r'^```[a-zA-Z]*\s*', '', sql_raw)
                        sql = re.sub(r'```$', '', sql.strip())
                        
                        # Store the prompt in session
                        prompt_data = {
                            'timestamp': datetime.now().isoformat(),
                            'type': 'SQL Generation',
                            'prompt': prompt,
                            'response': sql_raw,
                            'model': 'gpt-3.5-turbo',
                            'tokens': response.usage.total_tokens if hasattr(response, 'usage') else 'N/A',
                            'rule_text': rule_text
                        }
                        session['llm_prompts'].append(prompt_data)
                        session.modified = True  # Ensure session is saved
                        
                    except Exception as e:
                        error = f"OpenAI API error: {e}"
                elif action == 'test':
                    try:
                        sql_clean = sql
                        if sql_clean:
                            sql_clean = re.sub(r'^```[a-zA-Z]*\s*', '', sql_clean.strip())
                            sql_clean = re.sub(r'```$', '', sql_clean.strip())
                        result = con.execute(sql_clean).fetchdf()
                        test_result = result.to_string()
                        test_error = ''  # Clear error after successful run
                    except Exception as e:
                        test_error = str(e)
                elif action == 'fix':
                    try:
                        fix_prompt = prompt + f"\n\nDuckDB error: {test_error}\nPlease fix the SQL and output only the corrected SQL code."
                        response = openai.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are a helpful assistant that writes SQL queries for DuckDB."},
                                {"role": "user", "content": fix_prompt}
                            ],
                            max_tokens=512,
                            temperature=0.1
                        )
                        sql_raw = response.choices[0].message.content.strip()
                        # Remove markdown code block markers from LLM output
                        sql = re.sub(r'^```[a-zA-Z]*\s*', '', sql_raw)
                        sql = re.sub(r'```$', '', sql.strip())
                        
                        # Store the fix prompt in session
                        prompt_data = {
                            'timestamp': datetime.now().isoformat(),
                            'type': 'SQL Fix',
                            'prompt': fix_prompt,
                            'response': sql_raw,
                            'model': 'gpt-3.5-turbo',
                            'tokens': response.usage.total_tokens if hasattr(response, 'usage') else 'N/A',
                            'rule_text': rule_text,
                            'error': test_error
                        }
                        session['llm_prompts'].append(prompt_data)
                        session.modified = True  # Ensure session is saved
                        
                    except Exception as e:
                        error = f"OpenAI API error: {e}"
        except Exception as e:
            error = f"Unexpected error: {e}"
    
    # Ensure duckdb_columns is always defined even if it wasn't set earlier
    if 'duckdb_columns' not in locals() or duckdb_columns is None:
        duckdb_columns = {}
    
    # Get LLM prompts from session
    llm_prompts = session.get('llm_prompts', [])
        
    return render_template('rules.html', 
                         sql=sql, 
                         api_key=api_key, 
                         error=error, 
                         test_result=test_result, 
                         test_error=test_error, 
                         prompt=prompt, 
                         rule_text=rule_text, 
                         duckdb_columns=duckdb_columns,
                         llm_prompts=llm_prompts,
                         request=request)

@app.route('/clear_prompts', methods=['POST'])
def clear_prompts():
    """Clear the LLM prompts history"""
    session['llm_prompts'] = []
    session.modified = True
    return redirect(url_for('rules'))

@app.route('/download', methods=['POST'])
def download_results():
    
    sql = request.form.get('sql', '')
    download_format = request.form.get('format', 'csv')
    filename_base = request.form.get('filename', 'sql_results')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_base}_{timestamp}"
    
    # Create a connection to DuckDB and execute the SQL
    try:
        con = duckdb.connect()
        # First recreate the tables that were in memory
        filepaths = session.get('filepaths', [])
        mapping = session.get('mapping', None)
        file_path_map = {os.path.basename(fp): fp for fp in filepaths}
        
        if mapping:
            # Use mapped table and column names
            for key, mapinfo in mapping.items():
                table_name = re.sub(r'[^a-zA-Z0-9_]', '', mapinfo['table'].replace(' ', '_').replace('-', '_')).lower()
                filename, sheet = key.split('::')
                file_path = file_path_map[filename]
                xls = pd.ExcelFile(file_path)
                df = xls.parse(sheet)
                # Rename columns according to mapping
                col_map = {col['original']: col['safe'] for col in mapinfo['columns']}
                df = df.rename(columns=col_map)
                con.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM df")
        else:
            # Fallback to original sheet/column names
            for path in filepaths:
                xls = pd.ExcelFile(path)
                for sheet in xls.sheet_names:
                    df = xls.parse(sheet)
                    safe_sheet = re.sub(r'[^a-zA-Z0-9_]', '', sheet.replace(' ', '_').replace('-', '_')).lower()
                    con.execute(f"CREATE TABLE IF NOT EXISTS {safe_sheet} AS SELECT * FROM df")
        
        # Clean the SQL
        sql_clean = sql
        if sql_clean:
            sql_clean = re.sub(r'^```[a-zA-Z]*\s*', '', sql_clean.strip())
            sql_clean = re.sub(r'```$', '', sql_clean.strip())
            
        # Execute the SQL and get the DataFrame
        result_df = con.execute(sql_clean).fetchdf()
        
        # Set appropriate file extension and mimetype
        if download_format == 'csv':
            file_ext = '.csv'
            mimetype = 'text/csv'
            download_name = f"{filename}.csv"
        else:  # excel
            file_ext = '.xlsx'
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            download_name = f"{filename}.xlsx"
            
        # Create a temporary file with the correct extension
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_path = temp_file.name
            
        if download_format == 'csv':
            # Save as CSV
            result_df.to_csv(temp_path, index=False)
        else:  # excel
            try:
                # First check if openpyxl is available
                import importlib
                openpyxl_spec = importlib.util.find_spec('openpyxl')
                
                if openpyxl_spec is None:
                    # openpyxl is not installed
                    raise ImportError("openpyxl is not installed")
                
                # Try to use openpyxl engine
                result_df.to_excel(temp_path, index=False, engine='openpyxl')
                
            except ImportError:
                # Fall back to CSV if openpyxl is not installed
                try:
                    os.remove(temp_path)  # Remove the Excel file
                except:
                    pass  # Ignore if file doesn't exist
                
                # Create new temp file with CSV extension
                with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as csv_file:
                    temp_path = csv_file.name
                
                result_df.to_csv(temp_path, index=False)
                mimetype = 'text/csv'
                download_name = f"{filename}.csv"
                # Include note about missing dependency
                session['download_error'] = "Excel export requires openpyxl. Falling back to CSV format."
                
            except Exception as e:
                # Handle other Excel-related errors
                try:
                    os.remove(temp_path)  # Remove the Excel file
                except:
                    pass  # Ignore if file doesn't exist
                
                # Create new temp file with CSV extension
                with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as csv_file:
                    temp_path = csv_file.name
                
                result_df.to_csv(temp_path, index=False)
                mimetype = 'text/csv'
                download_name = f"{filename}.csv"
                # Include note about the error
                session['download_error'] = f"Error creating Excel file: {str(e)}. Falling back to CSV format."
                mimetype = 'text/csv'
                download_name = f"{filename}.csv"
                # Include note about the error
                session['download_error'] = f"Error creating Excel file: {str(e)}. Falling back to CSV format."
        
        return send_file(temp_path, mimetype=mimetype, as_attachment=True, download_name=download_name)
    
    except Exception as e:
        # If there's an error, redirect back to the rules page with an error message
        session['download_error'] = f"Error downloading results: {str(e)}"
        return redirect(url_for('rules'))

@app.route('/install_openpyxl', methods=['POST'])
def install_openpyxl():
    import subprocess
    import sys
    
    try:
        # Try to install openpyxl using pip
        subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
        session['download_error'] = "Successfully installed openpyxl! You can now download as Excel."
    except Exception as e:
        # If installation fails, show an error
        session['download_error'] = f"Failed to install openpyxl: {str(e)}"
    
    # Redirect back to the rules page
    return redirect(url_for('rules'))

def get_excel_data(filepaths):
    data = {}
    sheet_name_counter = {}  # Track sheet names across all files
    
    for path in filepaths:
        xls = pd.ExcelFile(path)
        data[os.path.basename(path)] = {}
        for sheet in xls.sheet_names:
            df = xls.parse(sheet)
            columns = []
            for col in df.columns:
                safe_col = re.sub(r'[^a-zA-Z0-9_]', '', col.replace(' ', '_').replace('-', '_')).lower()
                columns.append({'original': col, 'safe': safe_col})
            
            # Generate safe table name from sheet name
            base_safe_sheet = re.sub(r'[^a-zA-Z0-9_]', '', sheet.replace(' ', '_').replace('-', '_')).lower()
            
            # Handle duplicate sheet names by adding numbers
            if base_safe_sheet in sheet_name_counter:
                sheet_name_counter[base_safe_sheet] += 1
                safe_sheet = f"{base_safe_sheet}_{sheet_name_counter[base_safe_sheet]}"
            else:
                sheet_name_counter[base_safe_sheet] = 1
                safe_sheet = base_safe_sheet
            
            data[os.path.basename(path)][sheet] = {
                'columns': columns, 
                'safe_sheet': safe_sheet,
                'row_count': len(df)  # Add row count for display
            }
    return data

if __name__ == '__main__':
	app.run(debug=True, port=5001)