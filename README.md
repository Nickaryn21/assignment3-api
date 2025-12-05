# **📚 Book Library API — Authentication & Authorization**

A simple REST API built using **Python Flask** that manages a book library and demonstrates:

- **Secure User Registration**
- **HTTP Basic Authentication**
- **Protected Write Endpoints**
- **Owner-Only Update/Delete Authorization**
- **Persistent User Storage (users.json)**

This project extends Assignment 3 by implementing Authentication, Authorization, and Data Persistence.

---

## **🔧 Project Features**

### **1. Core CRUD (Assignment 3)**

- Get all books  
- Get a single book by ID  
- Add a new book  
- Update an existing book  
- Delete a book  
- Uses a structured Book data model  

---

### **2. Authentication & Authorization (Assignment 4)**

- User registration with password validation  
- Passwords hashed before storage  
- Basic Authentication required for write operations  
- Only the book owner can update/delete their book  
- Users persist in `users.json`  

---

## **🛠 Tech Stack**

- Python 3  
- Flask  
- Werkzeug (password hashing)  
- JSON file persistence  

---

# **🚀 API Usage & Screenshots in the folder**

Below are sample requests using **Postman**, with screenshots included.

---

## **1. Register a User**

**Endpoint:** `POST /register`  
**Description:** Creates a new user with a hashed password.

**Request Body:**
json
`{
  "username": "Nicole",
  "password": "Nic12345"
}`

## **2. Get Current User**

**Endpoint:** `GET /me`  
**Authentication:** Basic Auth (username + password)

## **3. Create a Book**

**Endpoint:** `POST /books`  
**Authentication:** Basic Auth required

**Request Body:**
json
`{
  "id": "BK777",
  "title": "Information System Magic",
  "author": "Nicole Karyn",
  "publisher": "UA Press",
  "year": 2025,
  "genre": "FET",
  "stock": 10
}`

## **4. Update a Book (Owner Only)**

**Endpoint:** `PUT /books/BK777`  
**Authentication:** Basic Auth required

**Request Body:**
json
`{
  "stock": 20
}`

## **5. Forbidden Update (Not Owner)**
Trying to update a book created by another user returns 403 Forbidden.

## **6. Delete a Book (Owner Only)**

**Endpoint**: `DELETE /books/BK777`
**Authentication**: Basic Auth required

---

## **📁 File Structure**
assignment4/
1. app.py
2. users.json
3. README.md
4. (screenshots)

---

## **✅ Running the API**

**Start the server: **python3 app.py
**API runs at: **http://127.0.0.1:5000