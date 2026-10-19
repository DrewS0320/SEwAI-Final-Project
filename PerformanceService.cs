
using System;

namespace MarioKartAnalyzer.Services
{
    public enum RaceMode
    {
        OnlineMultiplayer,
        TimeTrial
    }

    public class PerformanceService
    {
        // ==========================================
        // ONLINE MULTIPLAYER WEIGHTS
        // All weights should add up to 1.00 (100%)
        // ==========================================

        public double OnlineRaceWeight { get; set; } = 0.10;
        public double OnlineRouteWeight { get; set; } = 0.25;
        public double OnlineItemWeight { get; set; } = 0.20;
        public double OnlineCoinWeight { get; set; } = 0.15;
        public double OnlineDriftWeight { get; set; } = 0.20;
        public double OnlineLapWeight { get; set; } = 0.05;
        public double OnlineBuildWeight { get; set; } = 0.05;


        // ==========================================
        // TIME TRIAL WEIGHTS
        // All weights should add up to 1.00 (100%)
        // ==========================================

        public double TrialRouteWeight { get; set; } = 0.25;
        public double TrialMushroomWeight { get; set; } = 0.05;
        public double TrialCoinWeight { get; set; } = 0.15;
        public double TrialDriftWeight { get; set; } = 0.20;
        public double TrialLapWeight { get; set; } = 0.30;
        public double TrialBuildWeight { get; set; } = 0.05;


        // ==========================================
        // SCORE LIMITER
        // Keeps scores between 0 and 100
        // ==========================================

        private static double LimitScore(double value)
        {
            return Math.Clamp(value, 0, 100);
        }


        // ==========================================
        // RACE RESULT - ONLINE MULTIPLAYER ONLY
        // ==========================================

        public double CalculateRaceResultScore(
            int finishingPosition)
        {
            if (finishingPosition < 1 ||
                finishingPosition > 12)
            {
                throw new ArgumentOutOfRangeException(
                    nameof(finishingPosition),
                    "Finishing position must be between 1 and 12.");
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


        // ==========================================
        // ROUTE EFFICIENCY - BOTH MODES
        // ==========================================

        public double CalculateRouteScore(
            double racingLineAccuracy,
            double shortcutEfficiency,
            double offRoadAvoidance)
        {
            double score =
                LimitScore(racingLineAccuracy) * 0.55 +
                LimitScore(shortcutEfficiency) * 0.25 +
                LimitScore(offRoadAvoidance) * 0.20;

            return LimitScore(score);
        }


        // ==========================================
        // ITEM USAGE - ONLINE MULTIPLAYER ONLY
        // ==========================================

        public double CalculateOnlineItemScore(
            double offensiveUsage,
            double defensiveUsage,
            double strategicUsage,
            double itemAvoidance)
        {
            double score =
                LimitScore(offensiveUsage) * 0.25 +
                LimitScore(defensiveUsage) * 0.25 +
                LimitScore(strategicUsage) * 0.20 +
                LimitScore(itemAvoidance) * 0.30;

            return LimitScore(score);
        }


        // ==========================================
        // MUSHROOM USAGE - TIME TRIAL ONLY
        // ==========================================

        public double CalculateMushroomScore(
            double shortcutEffectiveness,
            double timingEfficiency)
        {
            double score =
                LimitScore(shortcutEffectiveness) * 0.70 +
                LimitScore(timingEfficiency) * 0.30;

            return LimitScore(score);
        }


        // ==========================================
        // COIN MANAGEMENT - BOTH MODES
        // ==========================================

        public double CalculateCoinScore(
            double averageCoins)
        {
            // Average coins held throughout the race.
            // Expected range: 0 to 10.
            //
            // Example:
            // Average coins = 9
            // Coin score = 90/100
            //
            // Coin losses naturally reduce the average.

            double coinScore =
                Math.Clamp(averageCoins, 0, 10) * 10;

            return LimitScore(coinScore);
        }


        // ==========================================
        // DRIFT EFFICIENCY - BOTH MODES
        // ==========================================

        public double CalculateDriftScore(
            double successfulDriftPercentage,
            double miniTurboEfficiency)
        {
            double score =
                LimitScore(successfulDriftPercentage) * 0.60 +
                LimitScore(miniTurboEfficiency) * 0.40;

            return LimitScore(score);
        }


        // ==========================================
        // LAP CONSISTENCY - BOTH MODES
        // ==========================================

        public double CalculateLapConsistencyScore(
            double lap1,
            double lap2,
            double lap3)
        {
            if (lap1 <= 0 || lap2 <= 0 || lap3 <= 0)
            {
                throw new ArgumentOutOfRangeException(
                    nameof(lap1),
                    "All lap times must be positive.");
            }

            double average =
                (lap1 + lap2 + lap3) / 3.0;

            double fastest =
                Math.Min(lap1, Math.Min(lap2, lap3));

            double slowest =
                Math.Max(lap1, Math.Max(lap2, lap3));

            double differencePercentage =
                ((slowest - fastest) / average) * 100;

            // Provisional penalty multiplier.
            double score =
                100 - differencePercentage * 5;

            return LimitScore(score);
        }


        // ==========================================
        // KART BUILD - BOTH MODES
        // ==========================================

        public double CalculateBuildScore(
            double speed,
            double acceleration,
            double handling,
            double traction)
        {
            double score =
                LimitScore(speed) * 0.30 +
                LimitScore(acceleration) * 0.30 +
                LimitScore(handling) * 0.25 +
                LimitScore(traction) * 0.15;

            return LimitScore(score);
        }


        // ==========================================
        // ONLINE MULTIPLAYER OVERALL SCORE
        // ==========================================

        public int CalculateOnlineMultiplayerScore(
            double raceScore,
            double routeScore,
            double itemScore,
            double coinScore,
            double driftScore,
            double lapScore,
            double buildScore)
        {
            double total =
                LimitScore(raceScore) * OnlineRaceWeight +
                LimitScore(routeScore) * OnlineRouteWeight +
                LimitScore(itemScore) * OnlineItemWeight +
                LimitScore(coinScore) * OnlineCoinWeight +
                LimitScore(driftScore) * OnlineDriftWeight +
                LimitScore(lapScore) * OnlineLapWeight +
                LimitScore(buildScore) * OnlineBuildWeight;

            return (int)Math.Round(
                LimitScore(total));
        }


        // ==========================================
        // TIME TRIAL OVERALL SCORE
        // ==========================================

        public int CalculateTimeTrialOverallScore(
            double routeScore,
            double mushroomScore,
            double coinScore,
            double driftScore,
            double lapScore,
            double buildScore)
        {
            double total =
                LimitScore(routeScore) * TrialRouteWeight +
                LimitScore(mushroomScore) * TrialMushroomWeight +
                LimitScore(coinScore) * TrialCoinWeight +
                LimitScore(driftScore) * TrialDriftWeight +
                LimitScore(lapScore) * TrialLapWeight +
                LimitScore(buildScore) * TrialBuildWeight;

            return (int)Math.Round(
                LimitScore(total));
        }


        // ==========================================
        // PERFORMANCE CLASSIFICATION
        // ==========================================

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
    }
}
