CREATE DATABASE  IF NOT EXISTS `marketplace_db` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `marketplace_db`;
-- MySQL dump 10.13  Distrib 8.0.46, for macos15 (arm64)
--
-- Host: localhost    Database: marketplace_db
-- ------------------------------------------------------
-- Server version	9.7.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
SET @MYSQLDUMP_TEMP_LOG_BIN = @@SESSION.SQL_LOG_BIN;
SET @@SESSION.SQL_LOG_BIN= 0;

--
-- GTID state at the beginning of the backup 
--

SET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ 'ccc1a808-7ad5-11f1-9bcb-8c8b15c6a3dd:1-127';

--
-- Table structure for table `bridge_campaign_target`
--

DROP TABLE IF EXISTS `bridge_campaign_target`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bridge_campaign_target` (
  `target_key` bigint NOT NULL AUTO_INCREMENT,
  `campaign_key` bigint NOT NULL,
  `target_type` varchar(20) NOT NULL,
  `target_value` varchar(100) NOT NULL,
  PRIMARY KEY (`target_key`),
  UNIQUE KEY `uq_campaign_target` (`campaign_key`,`target_type`,`target_value`),
  CONSTRAINT `bridge_campaign_target_ibfk_1` FOREIGN KEY (`campaign_key`) REFERENCES `dim_campaign` (`campaign_key`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `bridge_seller_review`
--

DROP TABLE IF EXISTS `bridge_seller_review`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bridge_seller_review` (
  `seller_key` bigint NOT NULL,
  `review_key` bigint NOT NULL,
  `order_id` varchar(50) NOT NULL,
  PRIMARY KEY (`seller_key`,`review_key`),
  KEY `review_key` (`review_key`),
  CONSTRAINT `bridge_seller_review_ibfk_1` FOREIGN KEY (`seller_key`) REFERENCES `dim_seller` (`seller_key`),
  CONSTRAINT `bridge_seller_review_ibfk_2` FOREIGN KEY (`review_key`) REFERENCES `fact_order_review` (`review_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `data_quality_issue`
--

DROP TABLE IF EXISTS `data_quality_issue`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `data_quality_issue` (
  `issue_id` bigint NOT NULL AUTO_INCREMENT,
  `rule_id` varchar(20) NOT NULL,
  `entity_type` varchar(50) NOT NULL,
  `entity_id` varchar(100) DEFAULT NULL,
  `issue_type` varchar(100) NOT NULL,
  `details` text,
  `detected_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `run_id` bigint DEFAULT NULL,
  PRIMARY KEY (`issue_id`),
  KEY `idx_dq_rule` (`rule_id`),
  KEY `idx_dq_run` (`run_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2511 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dim_campaign`
--

DROP TABLE IF EXISTS `dim_campaign`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dim_campaign` (
  `campaign_key` bigint NOT NULL AUTO_INCREMENT,
  `campaign_id` varchar(20) NOT NULL,
  `campaign_name` varchar(150) NOT NULL,
  `start_date` datetime NOT NULL,
  `end_date` datetime NOT NULL,
  `priority` int NOT NULL,
  PRIMARY KEY (`campaign_key`),
  UNIQUE KEY `campaign_id` (`campaign_id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dim_customer`
--

DROP TABLE IF EXISTS `dim_customer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dim_customer` (
  `customer_key` bigint NOT NULL AUTO_INCREMENT,
  `customer_id` varchar(50) NOT NULL,
  `customer_unique_id` varchar(50) NOT NULL,
  `zip_code_prefix` varchar(10) DEFAULT NULL,
  `city` varchar(100) DEFAULT NULL,
  `state` char(2) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `region` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`customer_key`),
  UNIQUE KEY `customer_id` (`customer_id`)
) ENGINE=InnoDB AUTO_INCREMENT=99442 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dim_date`
--

DROP TABLE IF EXISTS `dim_date`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dim_date` (
  `date_key` int NOT NULL,
  `full_date` date NOT NULL,
  `year` smallint NOT NULL,
  `month` tinyint NOT NULL,
  `day` tinyint NOT NULL,
  `quarter` tinyint NOT NULL,
  `day_of_week` tinyint NOT NULL,
  `is_weekend` tinyint(1) NOT NULL,
  PRIMARY KEY (`date_key`),
  UNIQUE KEY `full_date` (`full_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dim_product`
--

DROP TABLE IF EXISTS `dim_product`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dim_product` (
  `product_key` bigint NOT NULL AUTO_INCREMENT,
  `product_id` varchar(50) NOT NULL,
  `category_name` varchar(150) DEFAULT NULL,
  `category_name_english` varchar(150) DEFAULT NULL,
  `weight_g` decimal(12,2) DEFAULT NULL,
  `length_cm` decimal(12,2) DEFAULT NULL,
  `height_cm` decimal(12,2) DEFAULT NULL,
  `width_cm` decimal(12,2) DEFAULT NULL,
  PRIMARY KEY (`product_key`),
  UNIQUE KEY `product_id` (`product_id`)
) ENGINE=InnoDB AUTO_INCREMENT=32952 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dim_seller`
--

DROP TABLE IF EXISTS `dim_seller`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dim_seller` (
  `seller_key` bigint NOT NULL AUTO_INCREMENT,
  `seller_id` varchar(50) NOT NULL,
  `zip_code_prefix` varchar(10) DEFAULT NULL,
  `city` varchar(100) DEFAULT NULL,
  `state` char(2) DEFAULT NULL,
  `region` varchar(30) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`seller_key`),
  UNIQUE KEY `seller_id` (`seller_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3096 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fact_order`
--

DROP TABLE IF EXISTS `fact_order`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fact_order` (
  `order_key` bigint NOT NULL AUTO_INCREMENT,
  `order_id` varchar(50) NOT NULL,
  `customer_key` bigint NOT NULL,
  `purchase_date_key` int DEFAULT NULL,
  `order_status` varchar(30) NOT NULL,
  `purchase_timestamp` datetime NOT NULL,
  `approved_timestamp` datetime DEFAULT NULL,
  `delivered_carrier_timestamp` datetime DEFAULT NULL,
  `delivered_customer_timestamp` datetime DEFAULT NULL,
  `estimated_delivery_timestamp` datetime DEFAULT NULL,
  `revenue_eligible` tinyint(1) NOT NULL DEFAULT '0',
  `payment_total_brl` decimal(18,2) DEFAULT NULL,
  `net_cash_paid_brl` decimal(18,2) DEFAULT NULL,
  `payment_difference_brl` decimal(18,2) DEFAULT NULL,
  `delivery_business_days` int DEFAULT NULL,
  `is_on_time` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`order_key`),
  UNIQUE KEY `order_id` (`order_id`),
  KEY `fk_order_customer` (`customer_key`),
  KEY `fk_order_purchase_date` (`purchase_date_key`),
  KEY `idx_order_purchase_timestamp` (`purchase_timestamp`),
  KEY `idx_order_status` (`order_status`),
  CONSTRAINT `fk_order_customer` FOREIGN KEY (`customer_key`) REFERENCES `dim_customer` (`customer_key`),
  CONSTRAINT `fk_order_purchase_date` FOREIGN KEY (`purchase_date_key`) REFERENCES `dim_date` (`date_key`)
) ENGINE=InnoDB AUTO_INCREMENT=99442 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fact_order_item`
--

DROP TABLE IF EXISTS `fact_order_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fact_order_item` (
  `order_item_key` bigint NOT NULL AUTO_INCREMENT,
  `order_id` varchar(50) NOT NULL,
  `order_item_id` int NOT NULL,
  `seller_key` bigint NOT NULL,
  `product_key` bigint NOT NULL,
  `shipping_limit_timestamp` datetime DEFAULT NULL,
  `seller_delivery_status` varchar(20) DEFAULT NULL,
  `price_brl` decimal(18,2) NOT NULL,
  `freight_brl` decimal(18,2) NOT NULL,
  `gross_brl` decimal(18,2) NOT NULL,
  `commission_rate` decimal(10,6) DEFAULT NULL,
  `commission_brl` decimal(18,2) DEFAULT NULL,
  `commission_usd` decimal(18,2) DEFAULT NULL,
  `gross_usd` decimal(18,2) DEFAULT NULL,
  `campaign_key` bigint DEFAULT NULL,
  `fx_rate_date_used` date DEFAULT NULL,
  `fx_rate_brl_to_usd` decimal(18,6) DEFAULT NULL,
  `seller_customer_distance_km` decimal(12,3) DEFAULT NULL,
  PRIMARY KEY (`order_item_key`),
  UNIQUE KEY `uq_order_item` (`order_id`,`order_item_id`),
  KEY `fk_item_product` (`product_key`),
  KEY `fk_item_campaign` (`campaign_key`),
  KEY `idx_item_seller` (`seller_key`),
  KEY `idx_item_order` (`order_id`),
  CONSTRAINT `fk_item_campaign` FOREIGN KEY (`campaign_key`) REFERENCES `dim_campaign` (`campaign_key`),
  CONSTRAINT `fk_item_order` FOREIGN KEY (`order_id`) REFERENCES `fact_order` (`order_id`),
  CONSTRAINT `fk_item_product` FOREIGN KEY (`product_key`) REFERENCES `dim_product` (`product_key`),
  CONSTRAINT `fk_item_seller` FOREIGN KEY (`seller_key`) REFERENCES `dim_seller` (`seller_key`)
) ENGINE=InnoDB AUTO_INCREMENT=112651 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fact_order_payment`
--

DROP TABLE IF EXISTS `fact_order_payment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fact_order_payment` (
  `payment_key` bigint NOT NULL AUTO_INCREMENT,
  `order_id` varchar(50) NOT NULL,
  `payment_sequential` int NOT NULL,
  `payment_type` varchar(50) NOT NULL,
  `payment_installments` int DEFAULT NULL,
  `payment_value_brl` decimal(18,2) NOT NULL,
  PRIMARY KEY (`payment_key`),
  UNIQUE KEY `uq_payment` (`order_id`,`payment_sequential`),
  KEY `idx_payment_order` (`order_id`),
  CONSTRAINT `fk_payment_order` FOREIGN KEY (`order_id`) REFERENCES `fact_order` (`order_id`)
) ENGINE=InnoDB AUTO_INCREMENT=103887 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fact_order_review`
--

DROP TABLE IF EXISTS `fact_order_review`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fact_order_review` (
  `review_key` bigint NOT NULL AUTO_INCREMENT,
  `review_id` varchar(50) NOT NULL,
  `order_id` varchar(50) NOT NULL,
  `review_score` int NOT NULL,
  `review_creation_date` datetime DEFAULT NULL,
  `review_answer_timestamp` datetime NOT NULL,
  PRIMARY KEY (`review_key`),
  UNIQUE KEY `uq_review_order` (`review_id`,`order_id`),
  KEY `idx_review_order` (`order_id`)
) ENGINE=InnoDB AUTO_INCREMENT=98674 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `order_fx_mapping`
--

DROP TABLE IF EXISTS `order_fx_mapping`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `order_fx_mapping` (
  `order_id` varchar(50) NOT NULL,
  `fx_date` date DEFAULT NULL,
  `exchange_rate` decimal(18,6) DEFAULT NULL,
  PRIMARY KEY (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `pipeline_run`
--

DROP TABLE IF EXISTS `pipeline_run`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pipeline_run` (
  `run_id` bigint NOT NULL AUTO_INCREMENT,
  `start_date` date DEFAULT NULL,
  `end_date` date DEFAULT NULL,
  `started_at` datetime NOT NULL,
  `completed_at` datetime DEFAULT NULL,
  `status` varchar(20) NOT NULL,
  `rows_processed` bigint DEFAULT '0',
  `error_message` text,
  PRIMARY KEY (`run_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ref_brazil_state`
--

DROP TABLE IF EXISTS `ref_brazil_state`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ref_brazil_state` (
  `ibge_state_id` int NOT NULL,
  `state_code` char(2) NOT NULL,
  `state_name` varchar(100) NOT NULL,
  `region_name` varchar(30) NOT NULL,
  PRIMARY KEY (`ibge_state_id`),
  UNIQUE KEY `state_code` (`state_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ref_category_commission_override`
--

DROP TABLE IF EXISTS `ref_category_commission_override`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ref_category_commission_override` (
  `override_key` bigint NOT NULL AUTO_INCREMENT,
  `category_name_en` varchar(100) NOT NULL,
  `fixed_rate` decimal(10,6) NOT NULL,
  `effective_from` date NOT NULL,
  `effective_to` date DEFAULT NULL,
  `notes` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`override_key`),
  KEY `idx_category_override` (`category_name_en`,`effective_from`,`effective_to`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ref_commission_rate`
--

DROP TABLE IF EXISTS `ref_commission_rate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ref_commission_rate` (
  `commission_key` bigint NOT NULL AUTO_INCREMENT,
  `tier` varchar(20) NOT NULL,
  `rate` decimal(10,6) NOT NULL,
  `effective_from` date NOT NULL,
  `effective_to` date DEFAULT NULL,
  PRIMARY KEY (`commission_key`),
  KEY `idx_commission_tier_dates` (`tier`,`effective_from`,`effective_to`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ref_fx_rate`
--

DROP TABLE IF EXISTS `ref_fx_rate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ref_fx_rate` (
  `rate_date` date NOT NULL,
  `from_currency` char(3) NOT NULL,
  `to_currency` char(3) NOT NULL,
  `exchange_rate` decimal(18,6) NOT NULL,
  PRIMARY KEY (`rate_date`,`from_currency`,`to_currency`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ref_geolocation`
--

DROP TABLE IF EXISTS `ref_geolocation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ref_geolocation` (
  `zip_code_prefix` int NOT NULL,
  `median_latitude` decimal(10,7) NOT NULL,
  `median_longitude` decimal(10,7) NOT NULL,
  PRIMARY KEY (`zip_code_prefix`),
  KEY `idx_geo_coordinates` (`median_latitude`,`median_longitude`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ref_holiday`
--

DROP TABLE IF EXISTS `ref_holiday`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ref_holiday` (
  `holiday_date` date NOT NULL,
  `state` char(2) NOT NULL DEFAULT 'BR',
  `holiday_name` varchar(200) NOT NULL,
  `holiday_type` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`holiday_date`,`state`,`holiday_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `seller_monthly_tier`
--

DROP TABLE IF EXISTS `seller_monthly_tier`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `seller_monthly_tier` (
  `seller_key` bigint NOT NULL,
  `tier_month` date NOT NULL,
  `previous_month_revenue_brl` decimal(18,2) NOT NULL DEFAULT '0.00',
  `seller_tier` varchar(20) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`seller_key`,`tier_month`),
  KEY `idx_seller_tier_month` (`tier_month`),
  KEY `idx_seller_tier` (`seller_tier`),
  CONSTRAINT `seller_monthly_tier_ibfk_1` FOREIGN KEY (`seller_key`) REFERENCES `dim_seller` (`seller_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-11-02 19:57:20
