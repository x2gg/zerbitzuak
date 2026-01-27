-- MySQL dump 10.13  Distrib 8.0.43, for Linux (x86_64)
--
-- Host: localhost    Database: user_db
-- ------------------------------------------------------
-- Server version	8.0.43

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `login_attempts`
--

DROP TABLE IF EXISTS `login_attempts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `login_attempts` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ip` varchar(45) COLLATE utf8mb4_unicode_ci NOT NULL,
  `attempted_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `success` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `idx_user_ip_time` (`username`,`ip`,`attempted_at`)
) ENGINE=InnoDB AUTO_INCREMENT=96 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `login_attempts`
--

LOCK TABLES `login_attempts` WRITE;
/*!40000 ALTER TABLE `login_attempts` DISABLE KEYS */;
INSERT INTO `login_attempts` VALUES (1,'aaa','158.227.115.100','2025-10-04 11:02:10',0),(2,'aaa','158.227.115.100','2025-10-04 11:02:19',0),(3,'aaa','158.227.115.100','2025-10-04 11:02:24',0),(4,'aaa','158.227.115.100','2025-10-04 11:11:34',0),(5,'aaa','158.227.115.100','2025-10-04 11:16:37',0),(6,'aaa','158.227.115.100','2025-10-04 11:16:42',0),(7,'bbb','158.227.115.100','2025-10-04 18:34:44',1),(8,'bbb','158.227.115.100','2025-10-04 18:40:46',1),(9,'bbb','158.227.115.100','2025-10-04 18:42:14',1),(10,'xgo','158.227.115.100','2025-10-05 07:31:53',0),(11,'xgoo','158.227.115.100','2025-10-05 14:22:51',0),(12,'xgoo','158.227.115.100','2025-10-05 14:24:16',0),(13,'kaka','158.227.115.100','2025-10-06 17:28:18',1),(14,'admin','158.227.115.100','2025-10-07 08:07:01',1),(15,'admin','158.227.115.100','2025-10-07 08:20:48',1),(16,'kaka','158.227.115.100','2025-10-07 08:37:00',1),(17,'admin','158.227.115.100','2025-10-07 08:37:05',0),(18,'admin','158.227.115.100','2025-10-07 08:37:15',0),(19,'admin','158.227.115.100','2025-10-07 08:40:38',0),(20,'sdfghjk','158.227.115.100','2025-10-07 08:40:41',0),(21,'admin','158.227.115.100','2025-10-07 08:48:21',1),(22,'kaka','158.227.115.100','2025-10-07 09:10:17',0),(23,'kkaka','158.227.115.100','2025-10-07 09:11:21',0),(24,'admin','158.227.115.100','2025-10-07 09:12:50',1),(25,'admin','158.227.115.100','2025-10-07 09:12:57',1),(26,'admin','158.227.115.100','2025-10-07 09:28:21',1),(27,'admin','158.227.115.100','2025-10-07 09:46:29',1),(28,'admin','158.227.115.100','2025-10-07 09:56:30',1),(29,'admin','158.227.115.100','2025-10-07 10:07:40',1),(30,'admin','158.227.115.100','2025-10-07 10:21:13',1),(31,'admin','158.227.115.100','2025-10-07 10:28:05',1),(32,'admin','158.227.115.100','2025-10-07 10:45:30',1),(33,'admin','158.227.115.100','2025-10-07 10:47:30',1),(34,'kaka','158.227.115.100','2025-10-07 10:51:38',1),(35,'kaka','158.227.115.100','2025-10-07 10:55:01',0),(36,'kaka','158.227.115.100','2025-10-07 10:55:07',1),(37,'kaka','158.227.115.100','2025-10-07 10:57:18',1),(38,'admin','158.227.115.100','2025-10-07 10:57:59',1),(39,'admin','158.227.115.100','2025-10-07 11:14:30',1),(40,'admin','158.227.115.100','2025-10-07 14:10:31',1),(41,'admin','158.227.115.100','2025-10-07 14:10:31',1),(42,'admin','158.227.115.100','2025-10-07 14:10:31',1),(43,'admin','158.227.115.100','2025-10-07 14:10:31',1),(44,'admin','158.227.115.100','2025-10-07 14:10:34',1),(45,'admin','158.227.115.100','2025-10-07 14:10:49',0),(46,'admin','158.227.115.100','2025-10-07 14:10:55',1),(47,'kaka','158.227.115.100','2025-10-07 14:13:53',1),(48,'admin','158.227.115.100','2025-10-07 14:16:38',1),(49,'admin','158.227.115.100','2025-10-07 14:17:28',1),(50,'admin','158.227.115.100','2025-10-07 14:38:51',1),(51,'admin','158.227.115.100','2025-10-07 14:40:08',1),(52,'admin','158.227.115.100','2025-10-07 15:53:42',1),(53,'admin','158.227.115.100','2025-10-07 16:04:44',1),(54,'admin','158.227.115.100','2025-10-07 16:05:48',1),(55,'admin','158.227.115.100','2025-10-07 16:06:00',1),(56,'admin','158.227.115.100','2025-10-07 16:11:17',1),(57,'admin','158.227.115.100','2025-10-07 16:18:48',1),(58,'prueba_user','158.227.115.100','2025-10-08 10:11:49',1),(59,'admin','158.227.115.100','2025-10-08 10:12:11',1),(60,'admin','158.227.115.100','2025-10-08 10:12:25',1),(61,'admin','158.227.115.100','2025-10-08 10:13:02',0),(62,'admin','158.227.115.100','2025-10-08 10:13:05',1),(63,'admin','158.227.115.100','2025-10-08 10:17:19',1),(64,'admin','158.227.115.100','2025-10-08 10:18:25',1),(65,'admin','158.227.115.100','2025-10-08 10:21:50',1),(66,'admin','158.227.115.100','2025-10-08 10:22:40',1),(67,'admin','158.227.115.100','2025-10-08 10:29:50',1),(68,'admin','158.227.115.100','2025-10-08 10:32:58',1),(69,'admin','158.227.115.100','2025-10-08 10:33:40',1),(70,'admin','158.227.115.100','2025-10-08 10:35:28',1),(71,'admin','158.227.115.100','2025-10-08 10:36:42',1),(72,'admin','158.227.115.100','2025-10-12 08:35:51',1),(73,'xgo','95.22.238.32','2025-10-13 09:13:26',0),(74,'admin','158.227.115.100','2025-10-13 09:14:56',0),(75,'admin','158.227.115.100','2025-10-13 09:15:03',0),(76,'admin','158.227.115.100','2025-10-13 09:15:51',0),(77,'xgo','158.227.115.100','2025-10-13 09:31:34',1),(78,'admin','158.227.115.100','2025-10-13 10:45:37',1),(79,'admin','158.227.115.100','2025-10-13 11:26:17',0),(80,'admin','158.227.115.100','2025-10-13 11:26:24',0),(81,'admin','158.227.115.100','2025-10-13 16:41:12',1),(82,'admin','158.227.115.100','2025-10-14 15:36:30',1),(83,'proba','158.227.115.100','2025-10-14 21:08:08',0),(84,'kaka','158.227.115.100','2025-10-14 21:08:22',1),(85,'kaka','158.227.115.100','2025-10-14 21:16:45',1),(86,'kaka','172.23.0.1','2025-10-14 21:17:45',1),(87,'kaka','172.23.0.1','2025-10-15 07:49:38',1),(88,'Soraina','158.227.115.100','2025-10-28 08:12:10',1),(89,'Soraina','158.227.115.100','2025-10-28 08:19:56',1),(90,'xgoehu','158.227.115.100','2025-10-28 08:24:01',1),(91,'Soraina','158.227.115.100','2025-10-28 08:58:08',0),(92,'Soraina','158.227.115.100','2025-10-28 09:00:50',1),(93,'Soraina','158.227.115.100','2025-10-28 09:12:28',1),(94,'Soraina','158.227.115.100','2025-10-28 10:06:25',1),(95,'Soraina','158.227.115.100','2025-10-29 08:23:27',1);
/*!40000 ALTER TABLE `login_attempts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `login_locks`
--

DROP TABLE IF EXISTS `login_locks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `login_locks` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ip` varchar(45) COLLATE utf8mb4_unicode_ci NOT NULL,
  `locked_until` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_user_ip` (`username`,`ip`),
  KEY `idx_locked_until` (`locked_until`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `login_locks`
--

LOCK TABLES `login_locks` WRITE;
/*!40000 ALTER TABLE `login_locks` DISABLE KEYS */;
INSERT INTO `login_locks` VALUES (1,'aaa','158.227.115.100','2025-10-04 11:21:42');
/*!40000 ALTER TABLE `login_locks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `api_key_preview` varchar(64) DEFAULT NULL,
  `u_status` enum('active','pending','disabled') DEFAULT 'pending',
  `u_type` varchar(20) NOT NULL DEFAULT 'basic',
  `isFederated` tinyint(1) DEFAULT '0',
  `email_verified` tinyint(1) DEFAULT '0',
  `verification_code` varchar(6) DEFAULT NULL,
  `verification_code_expires` timestamp NULL DEFAULT NULL,
  `verification_attempts` int DEFAULT '0',
  `last_verification_sent` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `recovery_token` varchar(128) DEFAULT NULL,
  `recovery_token_expires` timestamp NULL DEFAULT NULL,
  `recovery_attempts` int DEFAULT '0',
  `last_recovery_sent` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  KEY `idx_username` (`username`),
  KEY `idx_email` (`email`),
  KEY `idx_verification` (`username`,`verification_code`,`verification_code_expires`),
  KEY `idx_users_recovery` (`email`,`recovery_token`,`recovery_token_expires`)
) ENGINE=InnoDB AUTO_INCREMENT=65 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (37,'kegiazabal001','kegiazabal001@ikasle.ehu.eus','Jcv...F8p','active','basic',1,1,NULL,NULL,0,NULL,'2025-10-01 18:21:48','2025-10-07 07:28:18',NULL,NULL,0,NULL),(38,'proba','proba@example.com',NULL,'active','basic',0,0,NULL,NULL,0,NULL,'2025-10-01 18:34:04','2025-10-01 19:57:42',NULL,NULL,0,NULL),(40,'xabier_goenaga','xabier.goenaga@ehu.eus','KeN...Jhc','active','basic',1,1,NULL,NULL,0,NULL,'2025-10-01 18:55:51','2025-10-27 16:28:19',NULL,NULL,0,NULL),(44,'kaka','kegiazabal@gmail.com',NULL,'active','basic',0,1,NULL,'2025-10-02 09:33:54',0,'2025-10-02 09:03:54','2025-10-02 09:03:54','2025-10-07 11:14:46','1UdLpYA0nepG9GTOmJl_Gn8VxHeeg3OjI4iR4M-AAJY','2025-10-03 07:38:06',0,'2025-10-03 07:08:06'),(57,'admin','admin@example.com',NULL,'active','pro',0,1,NULL,NULL,0,NULL,'2025-10-07 08:06:42','2025-10-07 08:06:42',NULL,NULL,0,NULL),(61,'xgo','xabier.goenaga.ehu@gmail.com',NULL,'pending','basic',0,0,'768180','2025-10-13 10:01:35',0,'2025-10-13 09:31:34','2025-10-13 09:31:34','2025-10-13 09:31:34',NULL,NULL,0,NULL),(62,'ainara_estarrona','ainara.estarrona@ehu.eus',NULL,'active','basic',1,1,NULL,NULL,0,NULL,'2025-10-27 09:03:25','2025-10-27 09:03:25',NULL,NULL,0,NULL),(63,'Soraina','ainaest@gmail.com',NULL,'pending','basic',0,0,'359775','2025-10-28 09:37:20',0,'2025-10-28 09:07:20','2025-10-28 08:12:10','2025-10-28 09:07:20',NULL,NULL,0,NULL),(64,'xgoehu','xabier.goenaga.ehu@ehu.eus',NULL,'pending','basic',0,0,'845062','2025-10-28 08:54:02',0,'2025-10-28 08:24:01','2025-10-28 08:24:01','2025-10-28 08:24:01',NULL,NULL,0,NULL);
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-10-29 10:44:15
