# Overview

This software is a utility to create a spreadsheet of healthcare items with all the identifiers needed to print a label. This is done by scanning the item's DI/UDI numbers. The software accomplishes this by utilizing AccessGUDID's api to gather the Version Model Number (VMN) and other device identifiers assigned to the DI/UDI passed to it.

These identifiers are then used to lookup additional identifiers from an oracle SQL database and an Item master unique to the hospital's supply chain.

The main purpose of writing this software was to give a real world example of how sql relational databases can be used to solve difficult and complex problems.

[Software Demo Video](https://vimeo.com/1063949685/4d64478be1?share=copy)

# Relational Database

* **Django Database:**

  The primary database (SQLite) stores Django models such as `ScanRecord` . The `ScanRecord` model holds scan details including barcode, brand name, device description, and associated metadata.
* **Local SQLite Databases:**

  Two additional SQLite databases are used:

  * **`items.db`:**

    This database contains an `items` table used in the `find_item_details` function. The table stores columns such as:

    * `Item Name`
    * `Item Description`
    * `Trading Partner Name`
    * `TP Item Number`
    * (Additional columns like Item Status, Template Name, Item Class Name, etc., are also part of the schema.)
  * **`gudid_devices.db`:**

    Accessed via the `lookup_local_db` function, this database stores device information with columns including `PrimaryDI` and `catalogNumber` among others.

# Development Environment

* **Programming Language & Framework:**

  Developed in Python using the Django web framework (Django 5.1.6), which provides the backbone for the web application, including URL routing, ORM, and templating.
* **Key Libraries & Tools:**

  * **Pandas:** Used for data manipulation and exporting scan history to Excel.
  * **Requests:** For making API calls to the AccessGUDID service.
  * **SQLite3:** For direct database queries to local SQLite databases (`items.db` and `gudid_devices.db`).
  * **Django Channels & Daphne:** To support WebSocket connections.
  * **Other Standard Libraries:** `os`, `re`, `json`, `datetime`, and `logging` for various utility tasks.
* **Development Tools:**

  The project is managed with Git, and development is done using VS Code.

# Useful Websites

* [AccessGUDID API Documentation](https://accessgudid.nlm.nih.gov/resources/home)
* [Django Documentation](https://docs.djangoproject.com/)
* [Pandas Documentation](https://pandas.pydata.org/docs/)
* [SQLite Documentation](https://www.sqlite.org/docs.html)

# Future Work

* **Error Handling:** Enhance error management for API calls, file uploads, and database operations.
* **Configuration Improvements:** Replace hardcoded file paths (e.g., for `items.db` and `gudid_devices.db`) with configurable settings or environment variables.
* **Security Enhancements:** Implement additional validations and sanitizations for file uploads and user inputs to improve security.
* **User Interface:** Refine the UI for better usability and consider adding user authentication.
* **Testing:** Develop automated tests for scan processing, database lookups, and file export functionalities.
* **Performance Optimization:** Improve performance for handling large datasets and optimize database queries.
* **WebSocket Integration:** Explore further integration of Django Channels for real-time updates or notifications.
