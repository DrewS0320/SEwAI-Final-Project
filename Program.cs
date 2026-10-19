
using System;
using MarioKartAnalyzer.Services;

class Program
{
    static void Main(string[] args)
    {
        PerformanceService service = new PerformanceService();


        // ==========================================
        // OPTIONAL WEIGHT ADJUSTMENTS FOR DEMO
        // ==========================================

        // Uncomment these to experiment with weights.
        // Always keep each mode's weights totaling 100%.

        // service.OnlineCoinWeight = 0.20;
        // service.OnlineRouteWeight = 0.20;


        // ==========================================
        // SELECT RACE MODE
        // ==========================================

        RaceMode mode = RaceMode.TimeTrial;

        // Change to RaceMode.TimeTrial
        // to demonstrate the other scoring system.


        // ==========================================
        // SHARED TEST VALUES
        // ==========================================

        // ROUTE EFFICIENCY
        double racingLineAccuracy = 90;
        double shortcutEfficiency = 90;
        double offRoadAvoidance = 90;

        // COIN MANAGEMENT
        double averageCoins = 9;

        // DRIFT EFFICIENCY
        double successfulDriftPercentage = 90;
        double miniTurboEfficiency = 90;

        // LAP CONSISTENCY (SECONDS)
        double lap1 = 90;
        double lap2 = 80;
        double lap3 = 40;

        // KART BUILD (NORMALIZED 0-100)
        double speed = 90;
        double acceleration = 90;
        double handling = 90;
        double traction = 90;


        // ==========================================
        // ONLINE MULTIPLAYER TEST VALUES
        // ==========================================

        int finishingPosition = 1;

        double offensiveUsage = 85;
        double defensiveUsage = 90;
        double strategicUsage = 80;
        double itemAvoidance = 75;


        // ==========================================
        // TIME TRIAL TEST VALUES
        // ==========================================

        double mushroomShortcutEffectiveness = 90;
        double mushroomTimingEfficiency = 85;


        // ==========================================
        // CALCULATE SHARED CATEGORY SCORES
        // ==========================================

        double routeScore =
            service.CalculateRouteScore(
                racingLineAccuracy,
                shortcutEfficiency,
                offRoadAvoidance);

        double coinScore =
            service.CalculateCoinScore(
                averageCoins);

        double driftScore =
            service.CalculateDriftScore(
                successfulDriftPercentage,
                miniTurboEfficiency);

        double lapScore =
            service.CalculateLapConsistencyScore(
                lap1,
                lap2,
                lap3);

        double buildScore =
            service.CalculateBuildScore(
                speed,
                acceleration,
                handling,
                traction);


        // ==========================================
        // DISPLAY HEADER
        // ==========================================

        Console.WriteLine("==========================================");
        Console.WriteLine("      MARIO KART PERFORMANCE ANALYZER     ");
        Console.WriteLine("==========================================");
        Console.WriteLine();

        Console.WriteLine($"MODE: {mode}");
        Console.WriteLine();

        int overallScore;


        // ==========================================
        // ONLINE MULTIPLAYER SCORING
        // ==========================================

        if (mode == RaceMode.OnlineMultiplayer)
        {
            double raceScore =
                service.CalculateRaceResultScore(
                    finishingPosition);

            double itemScore =
                service.CalculateOnlineItemScore(
                    offensiveUsage,
                    defensiveUsage,
                    strategicUsage,
                    itemAvoidance);

            overallScore =
                service.CalculateOnlineMultiplayerScore(
                    raceScore,
                    routeScore,
                    itemScore,
                    coinScore,
                    driftScore,
                    lapScore,
                    buildScore);

            Console.WriteLine(
                $"Finishing Position: {finishingPosition}");

            Console.WriteLine();
            Console.WriteLine("ONLINE MULTIPLAYER BREAKDOWN");
            Console.WriteLine();

            PrintCategory(
                "Race Result",
                service.OnlineRaceWeight,
                raceScore);

            PrintCategory(
                "Route Efficiency",
                service.OnlineRouteWeight,
                routeScore);

            PrintCategory(
                "Item Usage and Avoidance",
                service.OnlineItemWeight,
                itemScore);

            PrintCategory(
                "Coin Management",
                service.OnlineCoinWeight,
                coinScore);

            PrintCategory(
                "Drift Efficiency",
                service.OnlineDriftWeight,
                driftScore);

            PrintCategory(
                "Lap Consistency",
                service.OnlineLapWeight,
                lapScore);

            PrintCategory(
                "Kart Build",
                service.OnlineBuildWeight,
                buildScore);
        }


        // ==========================================
        // TIME TRIAL SCORING
        // ==========================================

        else
        {
            double mushroomScore =
                service.CalculateMushroomScore(
                    mushroomShortcutEffectiveness,
                    mushroomTimingEfficiency);

            overallScore =
                service.CalculateTimeTrialOverallScore(
                    routeScore,
                    mushroomScore,
                    coinScore,
                    driftScore,
                    lapScore,
                    buildScore);

            Console.WriteLine("TIME TRIAL BREAKDOWN");
            Console.WriteLine();

            PrintCategory(
                "Route Efficiency",
                service.TrialRouteWeight,
                routeScore);

            PrintCategory(
                "Mushroom Usage",
                service.TrialMushroomWeight,
                mushroomScore);

            PrintCategory(
                "Coin Management",
                service.TrialCoinWeight,
                coinScore);

            PrintCategory(
                "Drift Efficiency",
                service.TrialDriftWeight,
                driftScore);

            PrintCategory(
                "Lap Consistency",
                service.TrialLapWeight,
                lapScore);

            PrintCategory(
                "Kart Build",
                service.TrialBuildWeight,
                buildScore);
        }


        // ==========================================
        // DISPLAY OVERALL RESULTS
        // ==========================================

        Console.WriteLine();
        Console.WriteLine("------------------------------------------");

        Console.WriteLine(
            $"AVERAGE COINS: {averageCoins:F1}/10");

        Console.WriteLine(
            $"OVERALL SCORE: {overallScore}/100");

        Console.WriteLine(
            $"CLASSIFICATION: {service.ClassifyPerformance(overallScore)}");

        Console.WriteLine("==========================================");
    }


    // ==========================================
    // PRINT INDIVIDUAL CATEGORY RESULTS
    // ==========================================

    static void PrintCategory(
        string name,
        double weight,
        double score)
    {
        // Convert decimal weight into percentage.
        // Example: 0.15 becomes 15%.

        double percentage = weight * 100;

        Console.WriteLine(
            $"{name,-27} ({percentage,2:F0}%): {score,5:F1}/100");
    }
}
