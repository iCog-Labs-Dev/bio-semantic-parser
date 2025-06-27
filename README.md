# Bio Semantic Parsing

This project focuses on building a pipeline that automates the extraction and transformation of biological research data into a structured logical format using advanced Large Language Model (LLM) prompting techniques. 

By converting unstructured biomedical data into formal representations (MeTTa / First-Order Logic), the pipeline enables seamless integration into Atomspace — supporting efficient, data-driven reasoning and knowledge representation.

## ✨ Current Implementation

- **Data Source**: [GEO (Gene Expression Omnibus)](https://www.ncbi.nlm.nih.gov/geo/)
- **Functionality**:
  - Accepts a **GSE ID**
  - Loads the associated **paper abstract** from PubMed
  - Converts both the abstract and GSE metadata into **MeTTa format**
  - Prepares the data for **Atomspace representation**

## 🛠️ Installation & Usage

### 1. Clone the Repository

```bash
git clone https://github.com/iCog-Labs-Dev/bio-semantic-parser.git
cd bio-semantic-parser
```

### 2. Set Environment Variables

Create a `.env` file in the root directory of the frontend and backend folders and add the necessary keys.

### 3. Navigate to Backend Directory

```bash
cd Backend
```

### 4. Build Docker Containers

```bash
docker compose build
```

### 5. Start the Application

```bash
docker compose up
```

### 6. Access the Web Interface

After the build is complete and the server is running, open your browser and visit:

```
http://localhost:3030/
```

You should see the Bio Semantic Parsing interface ready to accept GSE IDs.

```

