-- SQL Sample 1
/*# 
        Example 1 - Creating a sample Employee table with below requirements
            Req 1: Create Employee Table with 6 Columns
                    Employee Number, First Name, Last Name, email, Age, Location
            Req 2: Column 1 as Employee Number as Primary key
            Req 3: Employee First Name and Last Name columns can't be null
            Req 4: Email -  Must not be empty, must be unique
                            Must contain "@samplemail.com"
                            
*/
/*Step 1: Create Schema and Tables along with Store Procedure*/
CREATE SCHEMA testdbs_schema;
use testdbs_schema;
create table employeeTable(employeeNumber int,firstName varchar(50),lastName varchar(50),email varchar(50),age int,locationDetails varchar(100));
select * from employeeTable;
desc employeeTable;
alter table employeeTable add constraint primary key(employeeNumber);
alter table employeeTable add constraint employeeNumber UNIQUE (employeeNumber);
/*Store Procedure 1
INSERT INTO employeeTable(employeeNumber,firstName,lastName,email,age,locationDetails)
VALUES (@MyCounter,'first_name1','last_name1',concat(firstName,'.',lastName,'@sampleemail.com'),RAND()*(70-20)+20,'City1'); */
DELIMITER //
CREATE PROCEDURE insertRowsToemployeeTable()   
BEGIN
DECLARE i INT DEFAULT 1;
DECLARE CityNumber INT DEFAULT 0;
WHILE i<=1000 DO
    SET CityNumber=FLOOR(RAND()*(10-1)+1);
    INSERT INTO employeeTable(employeeNumber,firstName,lastName,email,age,locationDetails)
     VALUES (i,concat('first_name',i),concat('last_name',i),concat(firstName,'.',lastName,'@sampleemail.com'),RAND()*(70-20)+20,concat('City',CityNumber));
    SET i=i+1;
END WHILE;
END;
DELIMITER;

-------------------------------------------------------------------------
/*Step 2: Cal the Procedure and see the table*/
-----
call insertRowsToemployeeTable();
select * from employeeTable;
-- OR 
EXECUTE insertRowsToemployeeTable()









SELECT ROW_NUMBER() OVER (ORDER BY Id) AS employeeNumber,* FROM employeeTable


