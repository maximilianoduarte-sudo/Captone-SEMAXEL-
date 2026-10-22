
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
DROP TABLE IF EXISTS `accounts_usuario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_usuario` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `rol` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `telefono` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_id` int NOT NULL,
  `empresa_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `accounts_usuario_empresa_id_dda5e2c6_fk_empresas_empresa_id` (`empresa_id`),
  CONSTRAINT `accounts_usuario_empresa_id_dda5e2c6_fk_empresas_empresa_id` FOREIGN KEY (`empresa_id`) REFERENCES `empresas_empresa` (`id`),
  CONSTRAINT `accounts_usuario_user_id_42ac2466_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `first_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext COLLATE utf8mb4_unicode_ci,
  `object_repr` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `model` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) COLLATE utf8mb4_unicode_ci NOT NULL,
  `session_data` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `empresas_empresa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `empresas_empresa` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombre` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `rut` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `codigo` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `direccion` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `comuna` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ciudad` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `region` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `telefono` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `correo` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `estado` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `fecha_creacion` datetime(6) NOT NULL,
  `fecha_actualizacion` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `rut` (`rut`),
  UNIQUE KEY `codigo` (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `mantenimiento_planmantenimiento`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `mantenimiento_planmantenimiento` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombre` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `descripcion` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `frecuencia` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `fecha_proxima` datetime(6) NOT NULL,
  `activo` tinyint(1) NOT NULL,
  `fecha_creacion` datetime(6) NOT NULL,
  `fecha_actualizacion` datetime(6) NOT NULL,
  `categoria_id` bigint NOT NULL,
  `sucursal_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `mantenimiento_planma_categoria_id_8c4e0520_fk_tickets_c` (`categoria_id`),
  KEY `mantenimiento_planma_sucursal_id_3320ad22_fk_sucursale` (`sucursal_id`),
  CONSTRAINT `mantenimiento_planma_categoria_id_8c4e0520_fk_tickets_c` FOREIGN KEY (`categoria_id`) REFERENCES `tickets_categoria` (`id`),
  CONSTRAINT `mantenimiento_planma_sucursal_id_3320ad22_fk_sucursale` FOREIGN KEY (`sucursal_id`) REFERENCES `sucursales_sucursal` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `mantenimiento_programacionmantenimiento`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `mantenimiento_programacionmantenimiento` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `fecha_programada` datetime(6) NOT NULL,
  `estado` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `fecha_ejecucion` datetime(6) DEFAULT NULL,
  `observaciones` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `plan_id` bigint NOT NULL,
  `ticket_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `mantenimiento_progra_plan_id_76259346_fk_mantenimi` (`plan_id`),
  KEY `mantenimiento_progra_ticket_id_3149cb29_fk_tickets_t` (`ticket_id`),
  CONSTRAINT `mantenimiento_progra_plan_id_76259346_fk_mantenimi` FOREIGN KEY (`plan_id`) REFERENCES `mantenimiento_planmantenimiento` (`id`),
  CONSTRAINT `mantenimiento_progra_ticket_id_3149cb29_fk_tickets_t` FOREIGN KEY (`ticket_id`) REFERENCES `tickets_ticket` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ofertas_ofertaticket`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ofertas_ofertaticket` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `estado` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `fecha_publicacion` datetime(6) NOT NULL,
  `fecha_vencimiento` datetime(6) DEFAULT NULL,
  `fecha_respuesta` datetime(6) DEFAULT NULL,
  `fecha_tomada` datetime(6) DEFAULT NULL,
  `observaciones` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `tecnico_id` bigint DEFAULT NULL,
  `ticket_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ticket_id` (`ticket_id`),
  KEY `ofertas_ofertaticket_tecnico_id_d2f246de_fk_tecnicos_tecnico_id` (`tecnico_id`),
  KEY `idx_oferta_estado` (`estado`),
  CONSTRAINT `ofertas_ofertaticket_tecnico_id_d2f246de_fk_tecnicos_tecnico_id` FOREIGN KEY (`tecnico_id`) REFERENCES `tecnicos_tecnico` (`id`),
  CONSTRAINT `ofertas_ofertaticket_ticket_id_90ce9f8a_fk_tickets_ticket_id` FOREIGN KEY (`ticket_id`) REFERENCES `tickets_ticket` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `sla_slapolicy`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sla_slapolicy` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `prioridad` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tiempo_maximo_respuesta` int unsigned NOT NULL,
  `tiempo_maximo_resolucion` int unsigned NOT NULL,
  `activo` tinyint(1) NOT NULL,
  `fecha_creacion` datetime(6) NOT NULL,
  `fecha_actualizacion` datetime(6) NOT NULL,
  `empresa_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_sla_empresa_prioridad` (`empresa_id`,`prioridad`),
  CONSTRAINT `sla_slapolicy_empresa_id_8d320db0_fk_empresas_empresa_id` FOREIGN KEY (`empresa_id`) REFERENCES `empresas_empresa` (`id`),
  CONSTRAINT `sla_slapolicy_chk_1` CHECK ((`tiempo_maximo_respuesta` >= 0)),
  CONSTRAINT `sla_slapolicy_chk_2` CHECK ((`tiempo_maximo_resolucion` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `sucursales_sucursal`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sucursales_sucursal` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombre` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `codigo` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `direccion` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `comuna` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ciudad` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `region` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `telefono` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `correo` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `estado` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `fecha_creacion` datetime(6) NOT NULL,
  `fecha_actualizacion` datetime(6) NOT NULL,
  `empresa_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_sucursal_codigo_por_empresa` (`empresa_id`,`codigo`),
  CONSTRAINT `sucursales_sucursal_empresa_id_94b67276_fk_empresas_empresa_id` FOREIGN KEY (`empresa_id`) REFERENCES `empresas_empresa` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `sucursales_sucursal_encargados`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sucursales_sucursal_encargados` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `sucursal_id` bigint NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `sucursales_sucursal_encargados_sucursal_id_user_id_4dd050dd_uniq` (`sucursal_id`,`user_id`),
  KEY `sucursales_sucursal_encargados_user_id_b6dd3eab_fk_auth_user_id` (`user_id`),
  CONSTRAINT `sucursales_sucursal__sucursal_id_8b581acd_fk_sucursale` FOREIGN KEY (`sucursal_id`) REFERENCES `sucursales_sucursal` (`id`),
  CONSTRAINT `sucursales_sucursal_encargados_user_id_b6dd3eab_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tecnicos_especialidad`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tecnicos_especialidad` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `descripcion` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `activo` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tecnicos_tecnico`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tecnicos_tecnico` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `telefono` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `documento` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `descripcion` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `estado` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `fecha_registro` datetime(6) NOT NULL,
  `fecha_actualizacion` datetime(6) NOT NULL,
  `usuario_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `usuario_id` (`usuario_id`),
  UNIQUE KEY `documento` (`documento`),
  KEY `idx_tecnico_estado` (`estado`),
  CONSTRAINT `tecnicos_tecnico_usuario_id_2af7caf2_fk_auth_user_id` FOREIGN KEY (`usuario_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tecnicos_tecnico_especialidades`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tecnicos_tecnico_especialidades` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tecnico_id` bigint NOT NULL,
  `especialidad_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `tecnicos_tecnico_especia_tecnico_id_especialidad__a037bb29_uniq` (`tecnico_id`,`especialidad_id`),
  KEY `tecnicos_tecnico_esp_especialidad_id_5d24ce45_fk_tecnicos_` (`especialidad_id`),
  CONSTRAINT `tecnicos_tecnico_esp_especialidad_id_5d24ce45_fk_tecnicos_` FOREIGN KEY (`especialidad_id`) REFERENCES `tecnicos_especialidad` (`id`),
  CONSTRAINT `tecnicos_tecnico_esp_tecnico_id_4906cbeb_fk_tecnicos_` FOREIGN KEY (`tecnico_id`) REFERENCES `tecnicos_tecnico` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tickets_calificacion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tickets_calificacion` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `puntuacion` smallint unsigned NOT NULL,
  `comentario` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `fecha_calificacion` datetime(6) NOT NULL,
  `tecnico_id` bigint NOT NULL,
  `orden_trabajo_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `orden_trabajo_id` (`orden_trabajo_id`),
  KEY `tickets_calificacion_tecnico_id_76373693_fk_tecnicos_tecnico_id` (`tecnico_id`),
  CONSTRAINT `tickets_calificacion_orden_trabajo_id_caabbfc3_fk_tickets_o` FOREIGN KEY (`orden_trabajo_id`) REFERENCES `tickets_ordentrabajo` (`id`),
  CONSTRAINT `tickets_calificacion_tecnico_id_76373693_fk_tecnicos_tecnico_id` FOREIGN KEY (`tecnico_id`) REFERENCES `tecnicos_tecnico` (`id`),
  CONSTRAINT `tickets_calificacion_chk_1` CHECK ((`puntuacion` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tickets_categoria`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tickets_categoria` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `descripcion` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `activo` tinyint(1) NOT NULL,
  `especialidad_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre` (`nombre`),
  KEY `tickets_categoria_especialidad_id_4e10d4c1_fk_tecnicos_` (`especialidad_id`),
  CONSTRAINT `tickets_categoria_especialidad_id_4e10d4c1_fk_tecnicos_` FOREIGN KEY (`especialidad_id`) REFERENCES `tecnicos_especialidad` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tickets_evidenciaticket`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tickets_evidenciaticket` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `archivo` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `nombre` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `fecha_subida` datetime(6) NOT NULL,
  `ticket_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tickets_evidenciaticket_ticket_id_468a8012_fk_tickets_ticket_id` (`ticket_id`),
  CONSTRAINT `tickets_evidenciaticket_ticket_id_468a8012_fk_tickets_ticket_id` FOREIGN KEY (`ticket_id`) REFERENCES `tickets_ticket` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tickets_ordentrabajo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tickets_ordentrabajo` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `estado` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `fecha_inicio` datetime(6) DEFAULT NULL,
  `fecha_fin` datetime(6) DEFAULT NULL,
  `diagnostico` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `trabajo_realizado` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `observaciones` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `costo_estimado` decimal(12,2) DEFAULT NULL,
  `costo_final` decimal(12,2) DEFAULT NULL,
  `fecha_creacion` datetime(6) NOT NULL,
  `fecha_actualizacion` datetime(6) NOT NULL,
  `oferta_id` bigint DEFAULT NULL,
  `tecnico_id` bigint NOT NULL,
  `ticket_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ticket_id` (`ticket_id`),
  KEY `idx_orden_estado` (`estado`),
  KEY `tickets_ordentrabajo_oferta_id_89686cd3_fk_ofertas_o` (`oferta_id`),
  KEY `tickets_ordentrabajo_tecnico_id_c887dbd0_fk_tecnicos_tecnico_id` (`tecnico_id`),
  CONSTRAINT `tickets_ordentrabajo_oferta_id_89686cd3_fk_ofertas_o` FOREIGN KEY (`oferta_id`) REFERENCES `ofertas_ofertaticket` (`id`),
  CONSTRAINT `tickets_ordentrabajo_tecnico_id_c887dbd0_fk_tecnicos_tecnico_id` FOREIGN KEY (`tecnico_id`) REFERENCES `tecnicos_tecnico` (`id`),
  CONSTRAINT `tickets_ordentrabajo_ticket_id_8cce0701_fk_tickets_ticket_id` FOREIGN KEY (`ticket_id`) REFERENCES `tickets_ticket` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tickets_ticket`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tickets_ticket` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `numero` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `prioridad` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `estado` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tipo` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `titulo` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `descripcion` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `fecha_creacion` datetime(6) NOT NULL,
  `fecha_actualizacion` datetime(6) NOT NULL,
  `fecha_limite_sla` datetime(6) DEFAULT NULL,
  `fecha_cierre` datetime(6) DEFAULT NULL,
  `informacion_adicional` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `categoria_id` bigint NOT NULL,
  `creador_id` int NOT NULL,
  `sucursal_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `numero` (`numero`),
  KEY `idx_ticket_estado` (`estado`),
  KEY `idx_ticket_prioridad` (`prioridad`),
  KEY `idx_ticket_sucursal` (`sucursal_id`),
  KEY `tickets_ticket_categoria_id_0a1509bc_fk_tickets_categoria_id` (`categoria_id`),
  KEY `tickets_ticket_creador_id_b29e7e91_fk_auth_user_id` (`creador_id`),
  CONSTRAINT `tickets_ticket_categoria_id_0a1509bc_fk_tickets_categoria_id` FOREIGN KEY (`categoria_id`) REFERENCES `tickets_categoria` (`id`),
  CONSTRAINT `tickets_ticket_creador_id_b29e7e91_fk_auth_user_id` FOREIGN KEY (`creador_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `tickets_ticket_sucursal_id_1c7ca710_fk_sucursales_sucursal_id` FOREIGN KEY (`sucursal_id`) REFERENCES `sucursales_sucursal` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tickets_tickethistorial`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tickets_tickethistorial` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `estado_anterior` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `estado_nuevo` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `comentario` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `fecha_cambio` datetime(6) NOT NULL,
  `ticket_id` bigint NOT NULL,
  `usuario_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tickets_tickethistorial_ticket_id_f4c39ded_fk_tickets_ticket_id` (`ticket_id`),
  KEY `tickets_tickethistorial_usuario_id_f0162cb5_fk_auth_user_id` (`usuario_id`),
  CONSTRAINT `tickets_tickethistorial_ticket_id_f4c39ded_fk_tickets_ticket_id` FOREIGN KEY (`ticket_id`) REFERENCES `tickets_ticket` (`id`),
  CONSTRAINT `tickets_tickethistorial_usuario_id_f0162cb5_fk_auth_user_id` FOREIGN KEY (`usuario_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

