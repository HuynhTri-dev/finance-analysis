# Mermaid Diagram Snippets for SA Documentation

Use the right diagram type for the right purpose. Place code blocks with ` ```mermaid ``` ` in your `.md` files — most renderers (GitHub, GitLab, VSCode preview…) will display them natively.

## 1. Use Case Diagram

Mermaid does not have a native UML use case notation; simulate it using `flowchart` with actor nodes (use subgraphs to group use cases within the system boundary):

```mermaid
flowchart LR
    Actor1((Customer))
    Actor2((Admin))
    subgraph System[Order Management System]
        UC1([View Products])
        UC2([Place Order])
        UC3([Manage Inventory])
    end
    Actor1 --> UC1
    Actor1 --> UC2
    Actor2 --> UC3
```

## 2. Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant BE as Backend API
    participant DB as Database

    User->>FE: Click "Login"
    FE->>BE: POST /auth/login
    BE->>DB: Verify credentials
    DB-->>BE: Result
    alt Login successful
        BE-->>FE: 200 OK + JWT token
        FE-->>User: Redirect to Dashboard
    else Invalid credentials
        BE-->>FE: 401 Unauthorized
        FE-->>User: Display error message
    end
```

## 3. Activity Diagram (using flowchart)

```mermaid
flowchart TD
    Start([Start]) --> A[User enters information]
    A --> B{Information valid?}
    B -->|Yes| C[Save to system]
    B -->|No| D[Display error]
    D --> A
    C --> End([End])
```

## 4. ERD (Entity Relationship Diagram)

```mermaid
erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ ORDER_ITEM : contains
    PRODUCT ||--o{ ORDER_ITEM : "included in"

    CUSTOMER {
        string customer_id PK
        string name
        string email
    }
    ORDER {
        string order_id PK
        string customer_id FK
        date order_date
        string status
    }
    PRODUCT {
        string product_id PK
        string name
        decimal price
    }
```

## 5. Wireframe (simulated with block layout)

Mermaid does not have a real wireframe engine — use `flowchart` with rectangular boxes representing layout regions, and clearly note that this is a low-fidelity mockup, not a real UI. If the user needs higher fidelity (actual colors, spacing), recommend switching to a visualization tool or HTML mockup rather than Mermaid.

```mermaid
flowchart TD
    subgraph Screen["Screen: Home Page"]
        direction TB
        Header["Header: Logo | Menu | Avatar"]
        Banner["Promotional Banner"]
        subgraph Content["Main Content"]
            direction LR
            Sidebar["Sidebar: Filters"]
            ProductList["Product List (grid)"]
        end
        Footer["Footer: Links | Copyright"]
    end
    Header --> Banner --> Content --> Footer
```

## Diagram Selection Guide
| Purpose | Diagram Type |
|---|---|
| Who does what with the system | Use Case |
| Interaction flow between components over time | Sequence |
| Business process flow / decision logic | Activity (or BPMN-style flowchart) |
| Data structure / table relationships | ERD |
| Screen layout at a rough level | Block-layout flowchart (not a substitute for Figma) |
