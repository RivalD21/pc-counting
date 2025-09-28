-- phpMyAdmin SQL Dump
-- version 5.1.1
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Waktu pembuatan: 28 Sep 2025 pada 00.08
-- Versi server: 5.7.33
-- Versi PHP: 7.4.19

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `people_counting`
--

-- --------------------------------------------------------

--
-- Struktur dari tabel `areas`
--

CREATE TABLE `areas` (
  `area_id` int(11) NOT NULL,
  `camera_id` int(11) NOT NULL DEFAULT '1',
  `area_nama` varchar(100) NOT NULL,
  `deskripsi` text,
  `polygon` json NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data untuk tabel `areas`
--

INSERT INTO `areas` (`area_id`, `camera_id`, `area_nama`, `deskripsi`, `polygon`, `is_active`, `timestamp`) VALUES
(1, 1, 'polygon', 'area for people counting', '[{\"x\": 152, \"y\": 116}, {\"x\": 152, \"y\": 116}, {\"x\": 157, \"y\": 252}, {\"x\": 400, \"y\": 258}, {\"x\": 387, \"y\": 113}]', 1, '2025-09-26 06:46:40');

-- --------------------------------------------------------

--
-- Struktur dari tabel `cameras`
--

CREATE TABLE `cameras` (
  `camera_id` bigint(20) UNSIGNED NOT NULL,
  `name` varchar(100) NOT NULL,
  `source_url` text,
  `location_note` varchar(255) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data untuk tabel `cameras`
--

INSERT INTO `cameras` (`camera_id`, `name`, `source_url`, `location_note`, `is_active`, `timestamp`) VALUES
(1, 'nol Km', 'https://cctvjss.jogjakota.go.id/malioboro/NolKm_Utara.stream/playlist.m3u8', 'Nol Km Malioboro utara', 1, '2025-09-25 14:05:08');

-- --------------------------------------------------------

--
-- Struktur dari tabel `counting`
--

CREATE TABLE `counting` (
  `counting_id` bigint(20) UNSIGNED NOT NULL,
  `camera_id` bigint(20) UNSIGNED NOT NULL,
  `masuk` int(11) NOT NULL DEFAULT '0',
  `keluar` int(11) NOT NULL DEFAULT '0',
  `dalam` int(11) NOT NULL DEFAULT '0',
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data untuk tabel `counting`
--

INSERT INTO `counting` (`counting_id`, `camera_id`, `masuk`, `keluar`, `dalam`, `timestamp`) VALUES
(1, 1, 8, 5, 3, '2025-09-27 12:26:40'),
(24, 1, 0, 0, 9, '2025-09-27 13:33:18'),
(25, 1, 0, 0, 3, '2025-09-27 13:33:28'),
(26, 1, 0, 1, 4, '2025-09-27 13:33:38'),
(27, 1, 1, 0, 9, '2025-09-27 13:33:48'),
(28, 1, 0, 0, 9, '2025-09-27 13:33:58'),
(29, 1, 0, 0, 0, '2025-09-27 21:44:59'),
(30, 1, 0, 0, 0, '2025-09-27 21:45:06');

-- --------------------------------------------------------

--
-- Struktur dari tabel `counts_agg`
--

CREATE TABLE `counts_agg` (
  `bucket_start` datetime NOT NULL,
  `area_id` bigint(20) UNSIGNED NOT NULL,
  `camera_id` bigint(20) UNSIGNED NOT NULL,
  `masuk` int(11) NOT NULL DEFAULT '0',
  `keluar` int(11) NOT NULL DEFAULT '0',
  `dalam` int(11) NOT NULL DEFAULT '0',
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data untuk tabel `counts_agg`
--

INSERT INTO `counts_agg` (`bucket_start`, `area_id`, `camera_id`, `masuk`, `keluar`, `dalam`, `last_update`) VALUES
('2025-09-26 08:41:48', 1, 1, 0, 0, 0, '2025-09-26 08:42:00');

-- --------------------------------------------------------

--
-- Struktur dari tabel `setting`
--

CREATE TABLE `setting` (
  `setting_id` int(11) NOT NULL,
  `websocket` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data untuk tabel `setting`
--

INSERT INTO `setting` (`setting_id`, `websocket`) VALUES
(1, 'ws://localhost:8080');

--
-- Indexes for dumped tables
--

--
-- Indeks untuk tabel `areas`
--
ALTER TABLE `areas`
  ADD PRIMARY KEY (`area_id`),
  ADD KEY `idx_areas_active` (`is_active`);

--
-- Indeks untuk tabel `cameras`
--
ALTER TABLE `cameras`
  ADD PRIMARY KEY (`camera_id`),
  ADD KEY `idx_cameras_active` (`is_active`);

--
-- Indeks untuk tabel `counting`
--
ALTER TABLE `counting`
  ADD PRIMARY KEY (`counting_id`);

--
-- Indeks untuk tabel `counts_agg`
--
ALTER TABLE `counts_agg`
  ADD PRIMARY KEY (`bucket_start`,`area_id`,`camera_id`),
  ADD KEY `fk_ca_camera` (`camera_id`);

--
-- Indeks untuk tabel `setting`
--
ALTER TABLE `setting`
  ADD PRIMARY KEY (`setting_id`);

--
-- AUTO_INCREMENT untuk tabel yang dibuang
--

--
-- AUTO_INCREMENT untuk tabel `areas`
--
ALTER TABLE `areas`
  MODIFY `area_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT untuk tabel `cameras`
--
ALTER TABLE `cameras`
  MODIFY `camera_id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT untuk tabel `counting`
--
ALTER TABLE `counting`
  MODIFY `counting_id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=31;

--
-- AUTO_INCREMENT untuk tabel `setting`
--
ALTER TABLE `setting`
  MODIFY `setting_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- Ketidakleluasaan untuk tabel pelimpahan (Dumped Tables)
--

--
-- Ketidakleluasaan untuk tabel `counts_agg`
--
ALTER TABLE `counts_agg`
  ADD CONSTRAINT `fk_ca_camera` FOREIGN KEY (`camera_id`) REFERENCES `cameras` (`camera_id`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
