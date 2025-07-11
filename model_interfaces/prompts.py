from pydantic import  BaseModel, Field

class GeminiPrompts(BaseModel):
    GEMINI_PROMPT_TEMPLATE: str = """You are an expert Laravel developer. I'm going to provide you with information about a simple Leave Management System built with Laravel. Your task is to understand its structure and functionality based on the file descriptions below.

    This application allows employees to apply for leave, and for an administrator (implicitly) to approve or reject these leave applications.

    Here's an outline of the key files and their purpose in this 'leave-management-laravel' project:

    1.  **`app/Http/Controllers/LeaveController.php`**:
        *   This is the main controller handling all actions related to leave management.
        *   `index()`: Displays a list of all leave applications.
        *   `applyForm()`: Shows the form for an employee to apply for leave.
        *   `apply()`: Processes the leave application submitted through the form and saves it to the database.
        *   `approve()`: Marks a specific leave application as 'approved'.
        *   `reject()`: Marks a specific leave application as 'rejected'.

    2.  **`app/Models/Leave.php`**:
        *   This is the Eloquent model representing a 'leave' record in the database.
        *   It defines which fields can be mass-assigned (e.g., `employee_name`, `start_date`, `end_date`, `reason`, `status`).

    3.  **`database/migrations/create_leaves_table.php`**:
        *   This migration file defines the schema for the `leaves` table in the database.
        *   It includes columns like `id`, `employee_name`, `start_date`, `end_date`, `reason`, `status` (pending, approved, rejected), and timestamps.

    4.  **`resources/views/leave/apply.blade.php`**:
        *   This is a Blade template file that renders the HTML form for users to submit a leave application.
        *   It includes input fields for employee name, start date, end date, and reason for leave.

    5.  **`resources/views/leave/index.blade.php`**:
        *   This Blade template displays all the leave applications.
        *   For each leave application, it shows details like employee name, dates, and current status.
        *   It also includes forms/buttons to 'Approve' or 'Reject' each leave application.

    6.  **`routes/web.php`**:
        *   This file defines all the web routes for the application.
        *   It maps specific URLs to the corresponding methods in the `LeaveController`. For example:
            *   `GET /leaves` maps to `LeaveController@index`.
            *   `GET /leaves/apply` maps to `LeaveController@applyForm`.
            *   `POST /leaves/apply` maps to `LeaveController@apply`.
            *   `POST /leaves/{{id}}/approve` maps to `LeaveController@approve`.
            *   `POST /leaves/{{id}}/reject` maps to `LeaveController@reject`.

        You will be given with the user query as well as the relevant code chunks that will be fetched from the databse.
        Your task is to identify the most relevent chunks out of the ones given to you and prepare a user response
        explaing about the code logic in the chunks.

    """

    QUERY_ANALYSIS_PROMPT: str = """You are a helpful assistant. The user will provide a question.
    Your tasks are:
    1. Determine if the question is a general knowledge question OR if it is likely related to a software codebase.
    2. If it's a general knowledge question and you can answer it directly, provide the answer.
    3. If it's likely related to a software codebase:
        a. Correct any grammatical errors in the question.
        b. Rephrase it for clarity if necessary, ensuring it's optimized for semantic search in a codebase.
        c. Do NOT answer the codebase-related question yourself.
    4. Respond STRICTLY in JSON format. Follow the JSON schema provided below to structure your response.
    {format_instructions}

    User Question: "{query}"

    JSON Response:"""

    DIFF_GENERATION_PROMPT: str= """You are an expert at providing code changes for a laravel project.You are given with the codebase outline. Your task is to generate a code change in the unified diff format based on the user's request and the provided code context.
            Analyze the user's request and the relevant code chunks. Determine what code needs to be added, removed, or modified.
            Generate the patch file with the changes. Provide the diff header line numbers accoridng to the chunk start and
            end line given in the chunk detail. The diff header line number should not be excedding the chunk end line
            Rules for the diff format:
            - Ensure to follow standard unidiff format
            - Start with `diff --git a/full/path/to/original/file b/full/path/to/modified/file`
            - Follow with `--- a/full/path/to/original/file`
            - Then `+++ b/full/path/to/modified/file`
            - Use `@@ ... @@` lines to indicate hunk headers (line numbers and counts).
            - Lines starting with `-` are removed lines.
            - Lines starting with `+` are added lines.
            - Lines starting with ` ` (a single space) are context lines (unchanged lines shown for context).
            - Ensure the diff is syntactically correct and can be applied using a standard patch tool.
            - When creating a Patchset using unidiff , it should not give any errors.For eg: Hunk is shorter than expected. This error comes because you atre not giving proper closing braclets for an open curly bracket.
            - If the request is unclear or cannot be fulfilled based on the context, provide an empty diff or explain why in a comment within the diff format (e.g., starting lines with `#`).

            ***Constraint***
            1. From the given code chunks, find the best match chunk for the user query and do the code changes.
            2. It is possible that code changes may be required in two or more different chuks in different fils.
            3. Provide all the relevant code changes at once.
            4. The diff should show the entire context (i.e., is the number of lines given in the header should matach with actualline changes),
                 not just the lines that have changed.
            5. Code start line and end line is given is the chunk, while creating the diff_header make sure 
                it is correct to correspond to line numbers.


            User Request: "{user_query}"

            Relevant Code Chunks:
            {context_chunks_string}

            Generate the unified diff below:
            """
    FULL_CODE_MODIFICATION_PROMPT: str ="""You are an expert Laravel developer. You will receive:
            1. A user request describing the desired change.
            2. The full text of a single method (signature + body.

            This application allows employees to apply for leave, and for an administrator (implicitly) to approve or          reject these leave applications.
        
            Here's an outline of the key files and their purpose in this 'leave-management-laravel' project:
        
            1.  **`app/Http/Controllers/LeaveController.php`**:
                *   This is the main controller handling all actions related to leave management.
                *   `index()`: Displays a list of all leave applications.
                *   `applyForm()`: Shows the form for an employee to apply for leave.
                *   `apply()`: Processes the leave application submitted through the form and saves it to the database.
                *   `approve()`: Marks a specific leave application as 'approved'.
                *   `reject()`: Marks a specific leave application as 'rejected'.

            2.  **`app/Models/Leave.php`**:
                *   This is the Eloquent model representing a 'leave' record in the database.
                *   It defines which fields can be mass-assigned (e.g., `employee_name`, `start_date`, `end_date`,         `reason`, `status`).

            3.  **`database/migrations/create_leaves_table.php`**:
                *   This migration file defines the schema for the `leaves` table in the database.
                *   It includes columns like `id`, `employee_name`, `start_date`, `end_date`, `reason`, `status` (pending,         approved, rejected), and timestamps.

            4.  **`resources/views/leave/apply.blade.php`**:
                *   This is a Blade template file that renders the HTML form for users to submit a leave application.
                *   It includes input fields for employee name, start date, end date, and reason for leave.
        
            5.  **`resources/views/leave/index.blade.php`**:
                *   This Blade template displays all the leave applications.
                *   For each leave application, it shows details like employee name, dates, and current status.
                *   It also includes forms/buttons to 'Approve' or 'Reject' each leave application.

             6.  **`routes/web.php`**:
                *   This file defines all the web routes for the application.
                *   It maps specific URLs to the corresponding methods in the `LeaveController`. For example:
                    *   `GET /leaves` maps to `LeaveController@index`.
                    *   `GET /leaves/apply` maps to `LeaveController@applyForm`.
                    *   `POST /leaves/apply` maps to `LeaveController@apply`.
                    *   `POST /leaves/{{id}}/approve` maps to `LeaveController@approve`.
                    *   `POST /leaves/{{id}}/reject` maps to `LeaveController@reject`.

            **Inputs**: Use type, name, file_path, content, metadata (e.g., visibility), dependencies.
            **Chunk Selection**: Identify the most related chunks via dependencies (e.g., models via App\\Models\\*).
            **Modifications**: Always check model chunks for fillable fields; include all fields in changes using          $request->validate().
            **Output**: For changes, strictly return the complete modified method (including signature and braces), no         diff, no explanation, using Laravel conventions.
            **Edge Cases**: If model chunks are missing, return: 'Need the model chunk to validate fields.'
        
            Rewrite the entire method to implement the requested change. Return **only** the complete updated method           (signature and body), nothing else.
        
            User Request:
            {user_query}

            Original Method:
            {context_chunks_string}
                
    """

    CHUNK_SELECTION_PROMPT : str = """You are an expert Laravel developer. You will be given:
        • A user request describing the desired code change.
        • A numbered list of up to 8 code snippets, each with its file path and its content.
        
        Reply with only the zero-based index (0–7) of the snippet that should be modified to satisfy the request.
        
        User Request:
        {user_query}
        
        Snippets:
        {snippet_list}
        """


gemini_prompts = GeminiPrompts()