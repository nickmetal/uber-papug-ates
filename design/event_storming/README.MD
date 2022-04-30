

## Week 1: Homework

1. archive week 0 data 

    > created week_0 directory

2. Create Business flows/use cases/Domain boundaries diagram 

    > https://miro.com/app/board/uXjVO6P_vIE=/?share_link_id=474448053047

3. Create Data model

    > Created next dir tree where: models.py - database entities, aggregates.py - command aggregates

    ```sh
    design
    └── event_storming
        ├── account_domain
        │   ├── aggregates.py
        │   └── models.py
        ├── analytic_domain
        │   └── aggregates.py
        └── task_domain
            ├── aggregates.py
            └── models.py
    ```

4. Define aggregates relationships/dependencies

    > see diagram relationships in item 2 diagram

5. define services
    1. task service
    2. account service
    3. analytic service
    4. scheduler 
    5. write database postgresql
    6. read database postgresql