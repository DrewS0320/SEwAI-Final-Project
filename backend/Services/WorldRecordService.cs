
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;

namespace MarioKartAnalyzer.Services
{
    public sealed class WorldRecordResult
    {
        public string Track { get; init; } = "";
        public int EngineClass { get; init; }
        public double TotalTimeSeconds { get; init; }
        public double[]? LapTimesSeconds { get; init; }
        public string? Player { get; init; }
        public string? DateSet { get; init; }
        public string SourceUrl { get; init; } = "";
        public string SnapshotDate { get; init; } = "";
    }

    public sealed class PaceBenchmarkResult
    {
        public double PaceRatio { get; init; }
        public double PercentageSlower { get; init; }
        public double PaceScore { get; init; }
        public string Band { get; init; } = "";
    }

    public class WorldRecordService
    {
        private sealed record PaceBand(
            string Name, double? MaxRatio);

        private sealed record ScoreAnchor(
            double Ratio, double Score);

        private readonly Dictionary<string, WorldRecordResult> records =
            new(StringComparer.OrdinalIgnoreCase);

        private readonly List<PaceBand> bands = new();
        private readonly List<ScoreAnchor> anchors = new();

        public WorldRecordService()
        {
            string folder = FindDataFolder();

            LoadRecords(Path.Combine(
                folder, "world_records.json"));

            LoadBenchmarks(Path.Combine(
                folder, "pace_benchmarks.json"));
        }

        // ==========================================
        // FIND THE DATA DIRECTORY
        // ==========================================

        private static string FindDataFolder()
        {
            string[] folders =
            {
                Path.Combine(
                    AppContext.BaseDirectory, "Data"),

                Path.GetFullPath(Path.Combine(
                    AppContext.BaseDirectory,
                    "..", "..", "..", "Data")),

                Path.Combine(
                    Directory.GetCurrentDirectory(),
                    "backend", "Data"),

                Path.Combine(
                    Directory.GetCurrentDirectory(), "Data")
            };

            foreach (string folder in folders)
            {
                if (File.Exists(Path.Combine(
                        folder, "world_records.json")) &&
                    File.Exists(Path.Combine(
                        folder, "pace_benchmarks.json")))
                {
                    return folder;
                }
            }

            throw new FileNotFoundException(
                "Place world_records.json and " +
                "pace_benchmarks.json together in backend/Data.");
        }

        private static string RecordKey(
            string track, int engineClass)
        {
            string normalized = new string(track
                .Where(char.IsLetterOrDigit)
                .Select(char.ToLowerInvariant)
                .ToArray());

            return $"{normalized}:{engineClass}";
        }

        // ==========================================
        // LOAD WORLD RECORD DATABASE
        // ==========================================

        private void LoadRecords(string path)
        {
            using JsonDocument document =
                JsonDocument.Parse(File.ReadAllText(path));

            JsonElement root = document.RootElement;

            string snapshotDate =
                root.GetProperty("snapshot_date").GetString() ?? "";

            foreach (JsonElement track in
                root.GetProperty("tracks").EnumerateArray())
            {
                string name =
                    track.GetProperty("name").GetString() ?? "";

                JsonElement trackRecords =
                    track.GetProperty("records");

                foreach (int cc in new[] { 150, 200 })
                {
                    if (!trackRecords.TryGetProperty(
                            cc.ToString(), out JsonElement data) ||
                        data.ValueKind != JsonValueKind.Object)
                    {
                        continue;
                    }

                    if (!data.TryGetProperty(
                            "total_seconds", out JsonElement totalField) ||
                        totalField.ValueKind != JsonValueKind.Number)
                    {
                        continue;
                    }

                    double total = totalField.GetDouble();

                    if (!double.IsFinite(total) || total <= 0)
                        continue;

                    double[]? splits = null;

                    if (data.TryGetProperty(
                            "lap_splits_seconds",
                            out JsonElement splitField) &&
                        splitField.ValueKind == JsonValueKind.Array)
                    {
                        double[] parsed = splitField
                            .EnumerateArray()
                            .Select(x => x.GetDouble())
                            .ToArray();

                        if (parsed.Length > 0 &&
                            parsed.All(x =>
                                double.IsFinite(x) && x > 0))
                        {
                            splits = parsed;
                        }
                    }

                    records.Add(
                        RecordKey(name, cc),
                        new WorldRecordResult
                        {
                            Track = name,
                            EngineClass = cc,
                            TotalTimeSeconds = total,
                            LapTimesSeconds = splits,
                            Player = OptionalString(
                                data, "record_holder"),
                            DateSet = OptionalString(
                                data, "record_date"),
                            SourceUrl = OptionalString(
                                data, "source_url") ?? "",
                            SnapshotDate = snapshotDate
                        });
                }
            }
        }

        // ==========================================
        // LOAD PERFORMANCE BANDS
        // ==========================================

        private void LoadBenchmarks(string path)
        {
            using JsonDocument document =
                JsonDocument.Parse(File.ReadAllText(path));

            JsonElement root = document.RootElement;

            if (root.GetProperty(
                    "is_empirical_player_distribution").GetBoolean())
            {
                throw new InvalidDataException(
                    "Expected project-defined benchmark bands, " +
                    "not player percentile data.");
            }

            foreach (JsonElement entry in
                root.GetProperty("bands").EnumerateArray())
            {
                JsonElement max =
                    entry.GetProperty("max_ratio");

                bands.Add(new PaceBand(
                    entry.GetProperty("name").GetString()
                        ?? "Unclassified",
                    max.ValueKind == JsonValueKind.Null
                        ? null
                        : max.GetDouble()));
            }

            foreach (JsonElement entry in
                root.GetProperty("score_anchors").EnumerateArray())
            {
                anchors.Add(new ScoreAnchor(
                    entry.GetProperty("ratio").GetDouble(),
                    entry.GetProperty("score").GetDouble()));
            }

            if (bands.Count == 0 ||
                anchors.Count < 2 ||
                anchors.Any(a =>
                    !double.IsFinite(a.Ratio) ||
                    !double.IsFinite(a.Score) ||
                    a.Ratio <= 0 ||
                    a.Score < 0 ||
                    a.Score > 100) ||
                anchors.Zip(
                    anchors.Skip(1),
                    (a, b) => b.Ratio <= a.Ratio).Any(x => x))
            {
                throw new InvalidDataException(
                    "Invalid pace_benchmarks.json configuration.");
            }
        }

        private static string? OptionalString(
            JsonElement obj, string key)
        {
            return obj.TryGetProperty(
                    key, out JsonElement value) &&
                value.ValueKind == JsonValueKind.String
                    ? value.GetString()
                    : null;
        }

        // ==========================================
        // LOOK UP A TRACK'S WORLD RECORD
        // ==========================================

        public WorldRecordResult GetRecord(
            string track, int engineClass)
        {
            if (records.TryGetValue(
                RecordKey(track, engineClass), out var result))
            {
                return result;
            }

            throw new NotSupportedException(
                $"No {engineClass}cc record found for '{track}'.");
        }

        // ==========================================
        // CALCULATE BENCHMARK-BASED PACE
        // ==========================================

        public PaceBenchmarkResult EvaluatePace(
            double playerTime, double recordTime)
        {
            if (!double.IsFinite(playerTime) ||
                !double.IsFinite(recordTime) ||
                playerTime <= 0 ||
                recordTime <= 0)
            {
                throw new ArgumentOutOfRangeException(
                    nameof(playerTime),
                    "Race times must be finite and positive.");
            }

            double ratio = playerTime / recordTime;

            string band = bands.FirstOrDefault(b =>
                !b.MaxRatio.HasValue ||
                ratio <= b.MaxRatio.Value)?.Name
                ?? "Unclassified";

            double score;

            if (ratio <= anchors[0].Ratio)
            {
                score = anchors[0].Score;
            }
            else if (ratio >= anchors[^1].Ratio)
            {
                score = anchors[^1].Score;
            }
            else
            {
                score = 0;

                for (int i = 1; i < anchors.Count; i++)
                {
                    ScoreAnchor left = anchors[i - 1];
                    ScoreAnchor right = anchors[i];

                    if (ratio <= right.Ratio)
                    {
                        double fraction =
                            (ratio - left.Ratio) /
                            (right.Ratio - left.Ratio);

                        score = left.Score + fraction *
                            (right.Score - left.Score);

                        break;
                    }
                }
            }

            return new PaceBenchmarkResult
            {
                PaceRatio = ratio,
                PercentageSlower = (ratio - 1) * 100,
                PaceScore = Math.Clamp(score, 0, 100),
                Band = band
            };
        }

        // ==========================================
        // WORLD RECORD COMPARISON HELPERS
        // ==========================================

        public double CalculateTimeDifference(
            double playerTime, double recordTime)
        {
            return playerTime - recordTime;
        }

        public double CalculateTimeDifferencePercentage(
            double playerTime, double recordTime)
        {
            return (playerTime / recordTime - 1) * 100;
        }
    }
}
