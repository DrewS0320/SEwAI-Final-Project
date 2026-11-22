
using System;
using System.IO;
using System.Linq;
using System.Text.Json;

namespace MarioKartAnalyzer.Services
{
    public sealed class VideoAnalysisResult
    {
        public string VideoName { get; init; } = "";
        public string Track { get; init; } = "";

        public double FinalTimeSeconds { get; init; }
        public string FinalTimeSource { get; init; } = "";

        public double[] LapTimesSeconds { get; init; } =
            Array.Empty<double>();

        public double AverageCoins { get; init; }

        // Percentage of the entire race assigned 10 coins.
        // Unresolved time is not counted as 10-coin time.
        public double? PercentageAtTenCoins { get; init; }

        // Retained for future use.
        public double? TimeAtTenCoinsSeconds { get; init; }

        public double? CoinTimeCoverage { get; init; }

        public int? StrongLossCandidates { get; init; }
        public int? PossibleCappedLosses { get; init; }
        public int? AmbiguousDecreases { get; init; }
    }

    public class VideoAnalysisService
    {
        // ==========================================
        // LOAD PYTHON VIDEO ANALYSIS RESULTS
        // ==========================================

        public VideoAnalysisResult LoadAnalysis(string jsonPath)
        {
            if (!File.Exists(jsonPath))
            {
                throw new FileNotFoundException(
                    "Could not find the Python analysis results.",
                    jsonPath);
            }

            using JsonDocument document =
                JsonDocument.Parse(
                    File.ReadAllText(jsonPath));

            JsonElement root = document.RootElement;

            string mode = ReadString(root, "mode", "");

            if (mode != "TimeTrial")
            {
                throw new InvalidDataException(
                    "Only Time Trial analysis is supported.");
            }

            double finalTime =
                ReadRequiredNumber(
                    root, "final_time_seconds");

            if (finalTime <= 0)
            {
                throw new InvalidDataException(
                    "Final race time must be positive.");
            }

            if (!root.TryGetProperty(
                    "lap_times_seconds_approx",
                    out JsonElement lapElement) ||
                lapElement.ValueKind != JsonValueKind.Array)
            {
                throw new InvalidDataException(
                    "Lap time data is missing.");
            }

            double[] laps = lapElement
                .EnumerateArray()
                .Select(element =>
                {
                    if (element.ValueKind != JsonValueKind.Number ||
                        !element.TryGetDouble(out double value) ||
                        !double.IsFinite(value) ||
                        value <= 0)
                    {
                        throw new InvalidDataException(
                            "A lap time is missing or invalid.");
                    }

                    return value;
                })
                .ToArray();

            if (laps.Length != 3)
            {
                throw new InvalidDataException(
                    "Expected exactly three lap times.");
            }

            double averageCoins =
                ReadRequiredNumber(root, "average_coins");

            if (averageCoins < 0 || averageCoins > 10)
            {
                throw new InvalidDataException(
                    "Average coins must be between 0 and 10.");
            }

            JsonElement coinV4 =
                root.TryGetProperty(
                    "coin_v4", out JsonElement v4)
                    ? v4
                    : default;

            JsonElement coinLoss =
                root.TryGetProperty(
                    "coin_loss_detection",
                    out JsonElement losses)
                    ? losses
                    : default;

            double? fractionAtTen =
                ReadOptionalNumber(
                    coinV4,
                    "fraction_of_race_time_assigned_10_coins");

            double? coverage =
                ReadOptionalNumber(
                    coinV4,
                    "time_coverage_fraction");

            if ((fractionAtTen.HasValue &&
                 (fractionAtTen.Value < 0 ||
                  fractionAtTen.Value > 1)) ||
                (coverage.HasValue &&
                 (coverage.Value < 0 ||
                  coverage.Value > 1)))
            {
                throw new InvalidDataException(
                    "Coin time fractions must be between 0 and 1.");
            }

            return new VideoAnalysisResult
            {
                VideoName = ReadString(
                    root,
                    "video_name",
                    Path.GetFileName(jsonPath)),

                Track = ReadString(
                    root,
                    "track",
                    "Unknown"),

                FinalTimeSeconds = finalTime,

                FinalTimeSource = ReadString(
                    root,
                    "final_time_source",
                    "unknown"),

                LapTimesSeconds = laps,

                AverageCoins = averageCoins,

                PercentageAtTenCoins =
                    fractionAtTen.HasValue
                        ? fractionAtTen.Value * 100.0
                        : null,

                TimeAtTenCoinsSeconds =
                    ReadOptionalNumber(
                        coinV4,
                        "time_at_10_coins_seconds_estimated"),

                CoinTimeCoverage = coverage,

                StrongLossCandidates =
                    ReadOptionalInteger(
                        coinLoss,
                        "strong_candidates"),

                PossibleCappedLosses =
                    ReadOptionalInteger(
                        coinLoss,
                        "possible_capped_losses"),

                AmbiguousDecreases =
                    ReadOptionalInteger(
                        coinLoss,
                        "ambiguous_decreases")
            };
        }

        // ==========================================
        // JSON HELPERS
        // ==========================================

        private static double ReadRequiredNumber(
            JsonElement element,
            string property)
        {
            if (element.ValueKind != JsonValueKind.Object ||
                !element.TryGetProperty(
                    property,
                    out JsonElement value) ||
                value.ValueKind != JsonValueKind.Number ||
                !value.TryGetDouble(out double number) ||
                !double.IsFinite(number))
            {
                throw new InvalidDataException(
                    $"Required field '{property}' is missing or invalid.");
            }

            return number;
        }

        private static double? ReadOptionalNumber(
            JsonElement element,
            string property)
        {
            if (element.ValueKind != JsonValueKind.Object ||
                !element.TryGetProperty(
                    property,
                    out JsonElement value) ||
                value.ValueKind != JsonValueKind.Number)
            {
                return null;
            }

            double number = value.GetDouble();

            return double.IsFinite(number)
                ? number
                : null;
        }

        private static int? ReadOptionalInteger(
            JsonElement element,
            string property)
        {
            if (element.ValueKind != JsonValueKind.Object ||
                !element.TryGetProperty(
                    property,
                    out JsonElement value) ||
                value.ValueKind != JsonValueKind.Number ||
                !value.TryGetInt32(out int number))
            {
                return null;
            }

            return number;
        }

        private static string ReadString(
            JsonElement element,
            string property,
            string fallback)
        {
            if (element.ValueKind != JsonValueKind.Object ||
                !element.TryGetProperty(
                    property,
                    out JsonElement value) ||
                value.ValueKind != JsonValueKind.String)
            {
                return fallback;
            }

            return value.GetString() ?? fallback;
        }
    }
}
