

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

5. Define services
    1. task service(async write + sync read)
    2. account service(async write + sync read)
    3. analytic service(sync read)
    4. scheduler(async write + sync read) 
    5. write database postgresql
    6. read database postgresql

6. Define business events(per domain)
    1. account_domain:
        1. day_total_calculated - produced by scheduler service
    2. analytic_domain:
        no events
    3. task_domain: 
        1. task_created - produced by task service
        2. tasks_assigned - produced by task service
        3. task_completed - produced by task service

7. Define CUD events + payload
    1. task_created_cud - produced by task service
    2. tasks_assigned_cud - produced by task service
    3. task_completed_cud - produced by task service
    4. day_total_calculated_cud - produced by scheduler service