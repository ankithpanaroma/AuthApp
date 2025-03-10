## How to run the app:

1. Create a venv and activate it.
3. cd into the backend, install all the requirements with ```pip install -r requirememnts.txt```
4. Start the backend ```uvicorn main:app --reload```
5. cd in frontend/auth-app and ```npm start``` to start the frontend.

   Note:
   - Rename ```.env.template``` to ```.env``` in the backend directory, and update your credentials accordingly.
   - Add your credentials in ```login.js``` and ```register.js``` files in the frontend/auth-app as well. 
