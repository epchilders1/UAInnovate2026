# **Project Sentinel: Final Presentation Checklist**

Teams will have **5 minutes** to demonstrate their solution. Use this checklist to ensure your presentation covers all the technical requirements defined in the rubric.

### **📋 Pre-Demo Setup**

* \[ \] Ensure your database is seeded with the provided historical\_avengers\_data.csv.  
* \[ \] Have your server logs or a "Debug View" ready to show (for the Security/PII component).  
* \[ \] Test your local environment; have a recorded video backup of the "Golden Path" just in case of a live demo failure.[Optional]

### **⏱️ The 5-Minute Pitch**

1. **The System Overview (1 Min):** \* Briefly explain your stack (e.g., "We used React, Node.js, and MongoDB").  
   * Show your high-level architecture: how data moves from the report to the dashboard.  
2. **The "Full Stack" Live Demo (2 Mins):**  
   * **The Input:** Submit a new field report from the UI (use a report from the JSON file or make your own).  
   * **The Flow:** Show the "Pending" status change to "Processed."  
   * **The Result:** Show the new data point appearing in your tables or charts.  
3. **Intelligence & Security (1 Min):**  
   * **ML Forecast:** Point to your trend graph. Explain the logic used to predict when a resource (e.g., Vibranium) will hit zero.  
   * **PII Redaction:** **CRITICAL.** Show the request sent to the LLM. Prove that hero names and phone numbers were redacted *before* leaving your server.  
4. **Q\&A (1 Min):**  
   * Be prepared to discuss your database schema choices or how you handled "Thanos Snap" anomalies in the data.

### **🛡️ Final Checks**

* \[ \] Does the UI update in real-time without a full page refresh?  
* \[ \] Is the "Admin" or "Analytics" view restricted or differentiated from the "Input" view?  
* \[ \] Are the graphs interactive (hover for details, zoom, or filters)?
* \[ \] Are you able to query the backend without the use of a front end via curl/postman/console?