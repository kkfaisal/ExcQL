# Sample SQL Queries for ExcQL Demo

## Data Structure Overview

### departments.xlsx
- **departments** tab: department_id, department_name, budget, location, manager_name, established_date
- **projects** tab: project_id, project_name, department_id, start_date, end_date, budget, status

### employees.xlsx
- **employees** tab: employee_id, first_name, last_name, email, phone, department_id, position, salary, hire_date, manager_id, status
- **performance_reviews** tab: review_id, employee_id, review_date, performance_score, goals_met, reviewer_id, comments
- **training_records** tab: training_id, employee_id, course_name, training_date, completion_status, score, instructor, cost

## Sample Questions to Ask the LLM

### Basic Queries

1. **"Show me all employees in the Engineering department"**
```sql
SELECT e.employee_id, e.first_name, e.last_name, e.position, e.salary
FROM employees e
JOIN departments d ON e.department_id = d.department_id
WHERE d.department_name = 'Engineering';
```

2. **"What is the average salary by department?"**
```sql
SELECT d.department_name, AVG(e.salary) as avg_salary, COUNT(e.employee_id) as employee_count
FROM employees e
JOIN departments d ON e.department_id = d.department_id
WHERE e.status = 'Active'
GROUP BY d.department_name
ORDER BY avg_salary DESC;
```

### Intermediate Queries

3. **"Show me employees who have completed training in the last 6 months"**
```sql
SELECT DISTINCT e.first_name, e.last_name, e.position, t.course_name, t.training_date
FROM employees e
JOIN training_records t ON e.employee_id = t.employee_id
WHERE t.completion_status = 'Completed' 
AND t.training_date >= DATE('2024-04-01')
ORDER BY t.training_date DESC;
```

4. **"Find departments with projects over budget (comparing project budget to department budget)"**
```sql
SELECT d.department_name, d.budget as dept_budget, 
       SUM(p.budget) as total_project_budget,
       (SUM(p.budget) - d.budget) as over_budget_amount
FROM departments d
JOIN projects p ON d.department_id = p.department_id
GROUP BY d.department_id, d.department_name, d.budget
HAVING SUM(p.budget) > d.budget
ORDER BY over_budget_amount DESC;
```

### Advanced Queries

5. **"Show top performing employees with their department and recent training"**
```sql
SELECT e.first_name, e.last_name, d.department_name, 
       AVG(pr.performance_score) as avg_performance,
       COUNT(t.training_id) as training_count,
       MAX(t.training_date) as latest_training
FROM employees e
JOIN departments d ON e.department_id = d.department_id
LEFT JOIN performance_reviews pr ON e.employee_id = pr.employee_id
LEFT JOIN training_records t ON e.employee_id = t.employee_id 
WHERE e.status = 'Active'
GROUP BY e.employee_id, e.first_name, e.last_name, d.department_name
HAVING AVG(pr.performance_score) >= 4.0
ORDER BY avg_performance DESC, training_count DESC;
```

6. **"Find employees who are managers and their team performance"**
```sql
SELECT mgr.first_name || ' ' || mgr.last_name as manager_name,
       mgr.position as manager_position,
       d.department_name,
       COUNT(emp.employee_id) as team_size,
       AVG(emp.salary) as avg_team_salary,
       AVG(pr.performance_score) as avg_team_performance
FROM employees mgr
JOIN employees emp ON mgr.employee_id = emp.manager_id
JOIN departments d ON mgr.department_id = d.department_id
LEFT JOIN performance_reviews pr ON emp.employee_id = pr.employee_id
WHERE mgr.status = 'Active' AND emp.status = 'Active'
GROUP BY mgr.employee_id, mgr.first_name, mgr.last_name, mgr.position, d.department_name
ORDER BY team_size DESC;
```

### Complex Analysis Queries

7. **"Department ROI analysis: training cost vs performance improvement"**
```sql
SELECT d.department_name,
       SUM(t.cost) as total_training_cost,
       AVG(pr.performance_score) as avg_performance,
       COUNT(DISTINCT e.employee_id) as employee_count,
       SUM(t.cost) / COUNT(DISTINCT e.employee_id) as training_cost_per_employee
FROM departments d
JOIN employees e ON d.department_id = e.department_id
LEFT JOIN training_records t ON e.employee_id = t.employee_id
LEFT JOIN performance_reviews pr ON e.employee_id = pr.employee_id
WHERE e.status = 'Active'
GROUP BY d.department_id, d.department_name
ORDER BY avg_performance DESC;
```

8. **"Project timeline analysis with team composition"**
```sql
SELECT p.project_name,
       d.department_name,
       p.status,
       p.start_date,
       p.end_date,
       p.budget,
       COUNT(e.employee_id) as team_members,
       AVG(e.salary) as avg_team_salary,
       AVG(pr.performance_score) as avg_team_performance
FROM projects p
JOIN departments d ON p.department_id = d.department_id
JOIN employees e ON d.department_id = e.department_id
LEFT JOIN performance_reviews pr ON e.employee_id = pr.employee_id
WHERE e.status = 'Active'
GROUP BY p.project_id, p.project_name, d.department_name, p.status, p.start_date, p.end_date, p.budget
ORDER BY p.start_date DESC;
```

## Questions You Can Ask ExcQL's LLM

### Simple Questions:
- "Show me all employees in Sales department"
- "What's the total budget for all projects?"
- "List all training courses completed this year"
- "Who are the highest paid employees?"

### Analytical Questions:
- "Which department has the highest average performance score?"
- "Show me employees who need training based on low performance scores"
- "What's the correlation between training completion and performance?"
- "Which projects are behind schedule?"

### Business Intelligence Questions:
- "Calculate ROI for each department based on salary costs vs project budgets"
- "Identify skill gaps by analyzing training records and performance reviews"
- "Show workforce planning insights by department growth trends"
- "Find optimal team compositions for future projects"

### Trending/Time-based Questions:
- "Show hiring trends by department over time"
- "Which employees haven't had performance reviews recently?"
- "What's the training completion rate by quarter?"
- "Show project completion timeline analysis"

## Tips for Testing ExcQL:
1. Start with simple queries and gradually increase complexity
2. Test referential integrity by joining tables
3. Try aggregations (SUM, AVG, COUNT)
4. Test date filtering and time-based analysis
5. Use the data to demonstrate business intelligence capabilities
