
using System;
using System.IO;
using System.Text.Json;
using MarioKartAnalyzer.Services;

class Program
{
    static int Main(string[] args)
    {
        if (args.Length != 2 ||
            !int.TryParse(args[1], out int engineClass) ||
            (engineClass != 150 && engineClass != 200))
        {
            Console.WriteLine(
                "Usage: dotnet run --project <project> -- " +
                "<score_input.json> <150|200>");

            return 1;
        }

        try
        {
            var analysisService = new VideoAnalysisService();
            var performanceService = new PerformanceService();
            var recordService = new WorldRecordService();

            VideoAnalysisResult race =
                analysisService.LoadAnalysis(args[0]);

            WorldRecordResult record =
                recordService.GetRecord(
                    race.Track, engineClass);

            PaceBenchmarkResult pace =
                recordService.EvaluatePace(
                    race.FinalTimeSeconds,
                    record.TotalTimeSeconds);

            // ==========================================
            // COIN MANAGEMENT SCORING
            //
            // Average coin score minus loss penalties.
            // ==========================================

            CoinManagementResult coin =
                performanceService.CalculateCoinManagementScore(
                    race.AverageCoins,
                    race.StrongLossCandidates,
                    race.PossibleCappedLosses);

            // ==========================================
            // LAP PERFORMANCE SCORING
            // ==========================================

            double consistencyScore =
                performanceService.CalculateLapConsistencyScore(
                    race.LapTimesSeconds[0],
                    race.LapTimesSeconds[1],
                    race.LapTimesSeconds[2]);

            double lapPerformanceScore =
                0.70 * pace.PaceScore +
                0.30 * consistencyScore;

            // ==========================================
            // OVERALL TIME TRIAL SCORE
            //
            // Uses adjusted coin management score.
            // ==========================================

            int overallScore =
                performanceService.CalculateTimeTrialOverallScore(
                    coin.FinalScore,
                    lapPerformanceScore);

            double weightSum =
                performanceService.TrialLapWeight +
                performanceService.TrialCoinWeight;

            double lapWeight =
                performanceService.TrialLapWeight / weightSum;

            double coinWeight =
                performanceService.TrialCoinWeight / weightSum;

            // ==========================================
            // HEADER
            // ==========================================

            Console.WriteLine(
                "==========================================");
            Console.WriteLine(
                "      MARIO KART PERFORMANCE ANALYZER     ");
            Console.WriteLine(
                "==========================================");

            Console.WriteLine();
            Console.WriteLine($"MODE: TimeTrial {engineClass}cc");
            Console.WriteLine($"VIDEO: {race.VideoName}");
            Console.WriteLine($"TRACK: {race.Track}");

            // ==========================================
            // RACE TIME AND BENCHMARK
            // ==========================================

            Console.WriteLine();
            Console.WriteLine("RACE TIME AND BENCHMARK");
            Console.WriteLine();

            Console.WriteLine(
                $"Player Time: {FormatTime(race.FinalTimeSeconds)}");

            Console.WriteLine(
                $"World Record: {FormatTime(record.TotalTimeSeconds)}");

            Console.WriteLine(
                $"Time Behind WR: " +
                $"{race.FinalTimeSeconds - record.TotalTimeSeconds:+0.000;-0.000;0.000}s");

            Console.WriteLine(
                $"Relative Pace: " +
                $"{pace.PercentageSlower:+0.00;-0.00;0.00}% vs WR");

            Console.WriteLine(
                $"Pace Band: {pace.Band}");

            Console.WriteLine(
                $"Benchmark Score: {pace.PaceScore:F1}/100");

            Console.WriteLine(
                $"Reference Snapshot: {record.SnapshotDate}");

            Console.WriteLine(
                $"Timing Source: {race.FinalTimeSource}");

            Console.WriteLine(
                "Pace bands are project-defined, not player percentiles.");

            // ==========================================
            // LAP / SECTION COMPARISON
            // ==========================================

            Console.WriteLine();
            Console.WriteLine("LAP / SECTION COMPARISON");

            if (record.LapTimesSeconds is double[] recordLaps &&
                recordLaps.Length == race.LapTimesSeconds.Length)
            {
                Console.WriteLine();

                Console.WriteLine(
                    $"{"Lap",-8} {"Player",10} {"WR",10} {"Difference",12}");

                for (int i = 0; i < recordLaps.Length; i++)
                {
                    double playerLap =
                        race.LapTimesSeconds[i];

                    double recordLap =
                        recordLaps[i];

                    double difference =
                        playerLap - recordLap;

                    Console.WriteLine(
                        $"{$"Lap {i + 1}",-8} " +
                        $"{playerLap,10:F3} " +
                        $"{recordLap,10:F3} " +
                        $"{difference,12:+0.000;-0.000;0.000}");
                }
            }
            else
            {
                Console.WriteLine();
                Console.WriteLine(
                    "WR lap splits unavailable for this course.");

                for (int i = 0; i < race.LapTimesSeconds.Length; i++)
                {
                    Console.WriteLine(
                        $"Player Lap {i + 1}: " +
                        $"{race.LapTimesSeconds[i]:F3}s");
                }
            }

            // ==========================================
            // COIN MANAGEMENT STATISTICS
            // ==========================================

            Console.WriteLine();
            Console.WriteLine("COIN MANAGEMENT");
            Console.WriteLine();

            Console.WriteLine(
                $"Average Coins: {race.AverageCoins:F3}/10");

            if (race.PercentageAtTenCoins.HasValue)
            {
                Console.WriteLine(
                    $"Race Time at 10 Coins: " +
                    $"{race.PercentageAtTenCoins.Value:F1}%");
            }
            else
            {
                Console.WriteLine(
                    "Race Time at 10 Coins: Not available");
            }

            if (race.CoinTimeCoverage.HasValue)
            {
                Console.WriteLine(
                    $"Coin Data Coverage: " +
                    $"{race.CoinTimeCoverage.Value * 100:F1}%");
            }

            // ==========================================
            // COIN LOSS DETECTION
            // ==========================================

            Console.WriteLine();
            Console.WriteLine("COIN LOSS DETECTION");
            Console.WriteLine();

            Console.WriteLine(
                $"Strong Candidates: " +
                $"{FormatCount(race.StrongLossCandidates)}");

            Console.WriteLine(
                $"Possible Capped Losses: " +
                $"{FormatCount(race.PossibleCappedLosses)}");

            Console.WriteLine(
                $"Ambiguous Decreases: " +
                $"{FormatCount(race.AmbiguousDecreases)}");

            Console.WriteLine();
            Console.WriteLine(
                $"Base Coin Score: {coin.BaseScore:F1}/100");

            if (coin.LossDataAvailable)
            {
                Console.WriteLine(
                    $"Candidate Loss Penalty: " +
                    $"-{coin.LossPenalty:F1} points");
            }
            else
            {
                Console.WriteLine(
                    "Candidate Loss Penalty: Not available");

                Console.WriteLine(
                    "Loss detection data is missing; " +
                    "no additional penalty applied.");
            }

            Console.WriteLine(
                $"Adjusted Coin Score: {coin.FinalScore:F1}/100");

            Console.WriteLine();
            Console.WriteLine(
                "Loss candidates are not verified collisions.");

            Console.WriteLine(
                "Loss penalties are provisional and " +
                "may overlap with average-coin penalties.");

            // ==========================================
            // PERFORMANCE BREAKDOWN
            // ==========================================

            Console.WriteLine();
            Console.WriteLine("TIME TRIAL PERFORMANCE BREAKDOWN");
            Console.WriteLine();

            Console.WriteLine(
                $"Pace Benchmark: {pace.PaceScore:F1}/100");

            Console.WriteLine(
                $"Lap Consistency: {consistencyScore:F1}/100");

            Console.WriteLine(
                "Lap Performance = 70% Pace + 30% Consistency");

            Console.WriteLine();

            PrintCategory(
                "Lap Performance",
                lapWeight,
                lapPerformanceScore);

            PrintCategory(
                "Coin Management",
                coinWeight,
                coin.FinalScore);

            Console.WriteLine();
            Console.WriteLine(
                "------------------------------------------");

            Console.WriteLine(
                $"PROVISIONAL PERFORMANCE INDEX: " +
                $"{overallScore}/100");

            Console.WriteLine();
            Console.WriteLine(
                "Scores use project-defined benchmark bands.");

            Console.WriteLine(
                "Times and coin measurements can contain " +
                "estimation error.");

            Console.WriteLine(
                "==========================================");

            return 0;
        }
        catch (Exception ex) when (
            ex is IOException
            or UnauthorizedAccessException
            or JsonException
            or ArgumentException
            or NotSupportedException
            or InvalidOperationException)
        {
            Console.Error.WriteLine($"Error: {ex.Message}");
            return 1;
        }
    }

    // ==========================================
    // TIME FORMATTING
    // ==========================================

    static string FormatTime(double seconds)
    {
        int minutes = (int)(seconds / 60);

        return $"{minutes}:{seconds - minutes * 60:00.000}";
    }

    // ==========================================
    // OPTIONAL EVENT COUNTS
    // ==========================================

    static string FormatCount(int? count)
    {
        return count?.ToString() ?? "Not available";
    }

    // ==========================================
    // CATEGORY SCORING OUTPUT
    // ==========================================

    static void PrintCategory(
        string name,
        double weight,
        double score)
    {
        Console.WriteLine(
            $"{name,-27} ({weight * 100,3:F0}%): " +
            $"{score,5:F1}/100");
    }
}
