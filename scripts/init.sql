/*
===============================================================================
Database Creation and Setup Script

Purpose: This script performs the initial setup of the Energy Trading database.
         It checks for an existing database with the same name and if found,
         forces all connections to close and drops the database before 
         creating a fresh one with the required schemas.

Database: DataWarehouse

Schemas Created:
         - bronze: Raw data ingestion layer (staging area)
         - silver: Cleaned and transformed data layer
         - gold: Business-ready data mart layer

Safety Features:
         - Checks for existing database before dropping
         - Forces disconnection of all active users with ROLLBACK
         - Uses GO statements to ensure batch separation

Usage Example:
         Run this script once at the beginning of the project to set up
         the database environment. All subsequent ETL processes will
         reference this database.
===============================================================================
*/

USE master;
GO

IF EXISTS(SELECT 1 FROM sys.databases WHERE name = 'EnergyTradingPipeline')
BEGIN
    ALTER DATABASE EnergyTradingPipeline SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE EnergyTradingPipeline;
END
GO

CREATE DATABASE EnergyTradingPipeline;
GO

USE EnergyTradingPipeline
GO

CREATE SCHEMA bronze;
GO
CREATE SCHEMA silver;
GO
CREATE SCHEMA gold;
GO