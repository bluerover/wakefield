CREATE DATABSE levelMonitor;

USE levelMonitor;

CREATE TABLE `level` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `mac` varchar(50) DEFAULT NULL,
  `timestamp` bigint(20) DEFAULT NULL,
  `level` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;