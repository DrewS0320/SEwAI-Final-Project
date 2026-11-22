
using System;

namespace MarioKartAnalyzer.Services
{
    public enum RaceMode
    {
        OnlineMultiplayer,
        TimeTrial
    }

    public sealed class CoinManagementResult
    {
        public double BaseScore { get; init; }
        public double LossPenalty { get; init; }
        public double FinalScore { get; init; }
        public bool LossDataAvailable { get; init; }
    }

    public class PerformanceService
    {
        // ==========================================
        // ONLINE MULTIPLAYER WEIGHTS
        // Preserved for future development.
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
        //
        // Active:
        // Lap performance and coin management.
        // ==========================================

        // public double TrialRouteWeight { get; set; } = 0.25;
        // public double TrialMushroomWeight { get; set; } = 0.05;

        public double TrialCoinWeight { get; set; } = 0.15;

        // public double TrialDriftWeight { get; set; } = 0.20;

        public double TrialLapWeight { get; set; } = 0.30;

        // public double TrialBuildWeight { get; set; } = 0.05;

        // ==========================================
        // PROVISIONAL COIN LOSS PENALTIES
        //
        // Strong candidates: 3 points each
        // Possible capped losses: 1 point each
        // Ambiguous decreases: no penalty
        //
        // These are not confirmed collision counts.
        // ==========================================

        public double StrongLossPenaltyPoints { get; set; } = 3.0;
        public double CappedLossPenaltyPoints { get; set; } = 1.0;
        public double MaximumLossPenalty { get; set; } = 15.0;

        private static double LimitScore(double value)
        {
            return Math.Clamp(value, 0, 100);
        }

        // ==========================================
        // RACE RESULT - ONLINE MULTIPLAYER
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
        // ROUTE EFFICIENCY - FUTURE FEATURE
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
        // ONLINE ITEM USAGE - FUTURE FEATURE
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
        // MUSHROOM USAGE - FUTURE FEATURE
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
        // BASE COIN SCORE
        //
        // Time-weighted average coins, scaled 0-100.
        // ==========================================

        public double CalculateCoinScore(double averageCoins)
        {
            if (!double.IsFinite(averageCoins) ||
                averageCoins < 0 ||
                averageCoins > 10)
            {
                throw new ArgumentOutOfRangeException(
                    nameof(averageCoins),
                    "Average coins must be between 0 and 10.");
            }

            return LimitScore(averageCoins * 10.0);
        }

        // ==========================================
        // ADJUSTED COIN MANAGEMENT SCORE
        //
        // Includes direct loss-candidate penalties.
        //
        // No candidate data:
        // Use the base score without assuming zero hits.
        // ==========================================

        public CoinManagementResult CalculateCoinManagementScore(
            double averageCoins,
            int? strongLossCandidates,
            int? possibleCappedLosses)
        {
            double baseScore = CalculateCoinScore(averageCoins);

            if (strongLossCandidates < 0 ||
                possibleCappedLosses < 0)
            {
                throw new ArgumentOutOfRangeException(
                    nameof(strongLossCandidates),
                    "Coin-loss counts cannot be negative.");
            }

            if (!double.IsFinite(StrongLossPenaltyPoints) ||
                !double.IsFinite(CappedLossPenaltyPoints) ||
                !double.IsFinite(MaximumLossPenalty) ||
                StrongLossPenaltyPoints < 0 ||
                CappedLossPenaltyPoints < 0 ||
                MaximumLossPenalty < 0)
            {
                throw new InvalidOperationException(
                    "Coin-loss penalties must be finite and nonnegative.");
            }

            bool available =
                strongLossCandidates.HasValue &&
                possibleCappedLosses.HasValue;

            double penalty = 0;

            if (available)
            {
                double rawPenalty =
                    strongLossCandidates!.Value *
                    StrongLossPenaltyPoints +
                    possibleCappedLosses!.Value *
                    CappedLossPenaltyPoints;

                penalty = Math.Min(
                    rawPenalty,
                    MaximumLossPenalty);
            }

            return new CoinManagementResult
            {
                BaseScore = baseScore,
                LossPenalty = penalty,
                FinalScore = LimitScore(baseScore - penalty),
                LossDataAvailable = available
            };
        }

        // ==========================================
        // DRIFT EFFICIENCY - FUTURE FEATURE
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
        // LAP CONSISTENCY
        //
        // Laps 2 and 3 only.
        // Lap 1 is a standing-start lap.
        // ==========================================

        public double CalculateLapConsistencyScore(
            double lap1,
            double lap2,
            double lap3)
        {
            if (!double.IsFinite(lap1) ||
                !double.IsFinite(lap2) ||
                !double.IsFinite(lap3) ||
                lap1 <= 0 ||
                lap2 <= 0 ||
                lap3 <= 0)
            {
                throw new ArgumentOutOfRangeException(
                    nameof(lap1),
                    "All lap times must be finite and positive.");
            }

            double averageFlyingLap = (lap2 + lap3) / 2.0;
            double difference = Math.Abs(lap2 - lap3);

            double differencePercentage =
                (difference / averageFlyingLap) * 100.0;

            double score =
                100.0 - differencePercentage * 5.0;

            return LimitScore(score);
        }

        // ==========================================
        // KART BUILD - FUTURE FEATURE
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

            return (int)Math.Round(LimitScore(total));
        }

        // ==========================================
        // TIME TRIAL OVERALL SCORE
        //
        // 66.67% lap performance
        // 33.33% adjusted coin management
        // ==========================================

        public int CalculateTimeTrialOverallScore(
            double coinScore,
            double lapScore)
        {
            double totalWeight =
                TrialCoinWeight + TrialLapWeight;

            if (!double.IsFinite(totalWeight) ||
                totalWeight <= 0 ||
                TrialCoinWeight < 0 ||
                TrialLapWeight < 0)
            {
                throw new InvalidOperationException(
                    "Scoring weights must be valid and positive in total.");
            }

            double total =
                (
                    LimitScore(coinScore) * TrialCoinWeight +
                    LimitScore(lapScore) * TrialLapWeight
                ) / totalWeight;

            return (int)Math.Round(LimitScore(total));
        }

        // ==========================================
        // PERFORMANCE CLASSIFICATION
        // ==========================================

        public string ClassifyPerformance(int score)
        {
            if (score >= 90) return "Elite";
            if (score >= 80) return "Great";
            if (score >= 70) return "Good";
            if (score >= 60) return "Average";
            if (score >= 50) return "Below Average";

            return "Poor";
        }
    }
}
