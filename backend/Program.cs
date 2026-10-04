using System;
using MarioKartAnalyzer.Services;

class Program
{
    static void Main(string[] args)
    {
        // Create the PerformanceService object
        PerformanceService performanceService = new PerformanceService();


        // ==========================================
        // TEST VALUES
        // Change these to experiment with the score
        // ==========================================

        int finishingPosition = 1;
        double routeAccuracy = 85;
        double itemUsageScore = 90;
        double coinScore = 95;


        // ==========================================
        // TEST INDIVIDUAL CATEGORY SCORES
        // ==========================================

        double raceScore =
            performanceService.CalculateRaceResultScore(finishingPosition);

        double routeScore =
            performanceService.CalculateRouteScore(routeAccuracy);

        double itemScore =
            performanceService.CalculateItemUsageScore(itemUsageScore);

        double calculatedCoinScore =
            performanceService.CalculateCoinScore(coinScore);


        Console.WriteLine("===== MARIO KART PERFORMANCE =====");
        Console.WriteLine();

        Console.WriteLine("Finishing Position: " + finishingPosition);
        Console.WriteLine("Race Result Score: " + raceScore);
        Console.WriteLine("Route Score: " + routeScore);
        Console.WriteLine("Item Usage Score: " + itemScore);
        Console.WriteLine("Coin Score: " + calculatedCoinScore);


        // ==========================================
        // CALCULATE OVERALL SCORE
        // ==========================================

        int overallScore =
            performanceService.CalculatePerformanceScore(
                finishingPosition,
                routeAccuracy,
                itemUsageScore,
                coinScore
            );


        // ==========================================
        // CLASSIFY PERFORMANCE
        // ==========================================

        string classification =
            performanceService.ClassifyPerformance(overallScore);


        Console.WriteLine();
        Console.WriteLine("Overall Score: " + overallScore + "/100");
        Console.WriteLine("Classification: " + classification);
    }
}