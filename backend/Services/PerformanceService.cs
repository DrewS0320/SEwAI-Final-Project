using System;

namespace MarioKartAnalyzer.Services
{
    public class PerformanceService
    {
        // ============================================================
        // WEIGHTS
        // All weights should add up to 1.00 (100%)
        // ============================================================

        private const double RaceResultWeight = 0.15;
        private const double RouteWeight = 0.40;
        private const double ItemUsageWeight = 0.25;
        private const double CoinWeight = 0.20;


        // ============================================================
        // OVERALL PERFORMANCE SCORE
        // Combines all category scores into one score from 0-100.
        // ============================================================

        public int CalculatePerformanceScore(
            int finishingPosition,
            double routeAccuracy,
            double itemUsageScore,
            double coinScore)
        {
            double raceResultScore = CalculateRaceResultScore(finishingPosition);
            double routeScore = CalculateRouteScore(routeAccuracy);
            double itemScore = CalculateItemUsageScore(itemUsageScore);
            double calculatedCoinScore = CalculateCoinScore(coinScore);

            double overallScore =
                (raceResultScore * RaceResultWeight) +
                (routeScore * RouteWeight) +
                (itemScore * ItemUsageWeight) +
                (calculatedCoinScore * CoinWeight);

            return (int)Math.Round(Math.Clamp(overallScore, 0, 100));
        }


        // ============================================================
        // RACE RESULT SCORE
        // Grades the player's finishing position.
        // ============================================================

        public double CalculateRaceResultScore(int finishingPosition)
        {
            // Temporary scoring system.
            // We can adjust this later based on race type,
            // number of racers, 150cc vs 200cc, etc.

            if (finishingPosition < 1 || finishingPosition > 12)
            {
                throw new ArgumentOutOfRangeException(
                    nameof(finishingPosition),
                    "Finishing position must be between 1 and 12."
                );
            }

            return finishingPosition switch
            {
                1 => 100,
                2 => 90,
                3 => 80,
                4 => 70,
                5 => 60,
                6 => 50,
                7 => 40,
                8 => 30,
                9 => 20,
                10 => 10,
                11 => 5,
                12 => 0,
                _ => 0
            };
        }


        // ============================================================
        // ROUTE SCORE
        // Measures how closely the player follows an optimal route.
        // ============================================================

        public double CalculateRouteScore(double routeAccuracy)
        {
            // For now, routeAccuracy is already a percentage from 0-100.
            //
            // Example:
            // 95 = player followed optimal route 95% of the time.
            //
            // Future calculations could consider:
            // - Time spent in suboptimal course areas
            // - Racing line accuracy
            // - Shortcut usage
            // - Off-road driving
            // - Falls from the course

            return Math.Clamp(routeAccuracy, 0, 100);
        }


        // ============================================================
        // ITEM USAGE SCORE
        // Measures how effectively the player uses items.
        // ============================================================

        public double CalculateItemUsageScore(double itemUsageScore)
        {
            // For now, itemUsageScore is supplied as a 0-100 score.
            //
            // Eventually this function can calculate the score using:
            //
            // - Green shell accuracy
            // - Banana hits
            // - Fireball hits
            // - Defensive item usage
            // - Mushroom shortcut usage
            // - Blue shell dodging
            // - Super horn management
            // - Coin/item box management
            // - Strategic item holding

            return Math.Clamp(itemUsageScore, 0, 100);
        }


        // ============================================================
        // COIN MANAGEMENT SCORE
        // Measures how effectively the player maintains coins.
        // ============================================================

        public double CalculateCoinScore(double coinScore)
        {
            // For now, coinScore is supplied as a 0-100 score.
            //
            // Eventually this could be calculated using:
            //
            // - Average coins held during race
            // - Percentage of race spent at 10 coins
            // - Speed of recovering coins after being hit
            // - Avoiding unnecessary coin loss

            return Math.Clamp(coinScore, 0, 100);
        }


        // ============================================================
        // PERFORMANCE CLASSIFICATION
        // Gives the numerical score a readable classification.
        // ============================================================

        public string ClassifyPerformance(int score)
        {
            if (score >= 90)
                return "Elite";

            if (score >= 80)
                return "Great";

            if (score >= 70)
                return "Good";

            if (score >= 60)
                return "Average";

            if (score >= 50)
                return "Below Average";

            return "Poor";
        }


        // ============================================================
        // FUTURE SCORING FUNCTIONS
        // These are planned features and can be implemented later.
        // ============================================================

        /*
        public double CalculateDriftScore(...)
        {
            // Drift accuracy
            // Mini-turbo efficiency
            // Drift timing
            return 0;
        }


        public double CalculateLapConsistencyScore(...)
        {
            // Compare lap times on loop tracks.
            return 0;
        }


        public double CalculateBuildScore(...)
        {
            // Character + kart combination optimization.
            return 0;
        }


        public double CalculateTimeTrialScore(...)
        {
            // Compare time against known benchmark times.
            return 0;
        }
        */
    }
}