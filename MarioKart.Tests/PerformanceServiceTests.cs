using System;
using MarioKartAnalyzer.Services;
using Xunit;

namespace MarioKart.Tests
{
    public class PerformanceServiceTests
    {
        private readonly PerformanceService _service = new PerformanceService();

        // ---------- CalculateRaceResultScore ----------

        [Theory]
        [InlineData(1, 100)]
        [InlineData(2, 90)]
        [InlineData(3, 80)]
        [InlineData(4, 70)]
        [InlineData(5, 60)]
        [InlineData(6, 50)]
        [InlineData(7, 40)]
        [InlineData(8, 30)]
        [InlineData(9, 20)]
        [InlineData(10, 10)]
        [InlineData(11, 5)]
        [InlineData(12, 0)]
        public void CalculateRaceResultScore_ValidPosition_ReturnsExpectedScore(int position, double expected)
        {
            Assert.Equal(expected, _service.CalculateRaceResultScore(position));
        }

        [Theory]
        [InlineData(0)]
        [InlineData(-1)]
        [InlineData(13)]
        [InlineData(100)]
        public void CalculateRaceResultScore_OutOfRange_Throws(int position)
        {
            var ex = Assert.Throws<ArgumentOutOfRangeException>(
                () => _service.CalculateRaceResultScore(position));
            Assert.Equal("finishingPosition", ex.ParamName);
        }

        // ---------- Route / Item / Coin (clamp to 0-100) ----------

        [Theory]
        [InlineData(-10, 0)]
        [InlineData(0, 0)]
        [InlineData(55.5, 55.5)]
        [InlineData(100, 100)]
        [InlineData(150, 100)]
        public void CalculateRouteScore_ClampsToZeroToHundred(double input, double expected)
        {
            Assert.Equal(expected, _service.CalculateRouteScore(input));
        }

        [Theory]
        [InlineData(-10, 0)]
        [InlineData(0, 0)]
        [InlineData(72.25, 72.25)]
        [InlineData(100, 100)]
        [InlineData(250, 100)]
        public void CalculateItemUsageScore_ClampsToZeroToHundred(double input, double expected)
        {
            Assert.Equal(expected, _service.CalculateItemUsageScore(input));
        }

        [Theory]
        [InlineData(-5, 0)]
        [InlineData(0, 0)]
        [InlineData(33.3, 33.3)]
        [InlineData(100, 100)]
        [InlineData(101, 100)]
        public void CalculateCoinScore_ClampsToZeroToHundred(double input, double expected)
        {
            Assert.Equal(expected, _service.CalculateCoinScore(input));
        }

        // ---------- CalculatePerformanceScore ----------
        // Weights: race 15%, route 40%, items 25%, coins 20%

        [Fact]
        public void CalculatePerformanceScore_PerfectRace_Returns100()
        {
            Assert.Equal(100, _service.CalculatePerformanceScore(1, 100, 100, 100));
        }

        [Fact]
        public void CalculatePerformanceScore_WorstRace_Returns0()
        {
            Assert.Equal(0, _service.CalculatePerformanceScore(12, 0, 0, 0));
        }

        [Fact]
        public void CalculatePerformanceScore_MixedInputs_AppliesWeights()
        {
            // 100*.15 + 80*.40 + 60*.25 + 40*.20 = 15 + 32 + 15 + 8 = 70
            Assert.Equal(70, _service.CalculatePerformanceScore(1, 80, 60, 40));
        }

        [Fact]
        public void CalculatePerformanceScore_MidPack_AppliesWeights()
        {
            // 50*.15 + 50*.40 + 50*.25 + 50*.20 = 50
            Assert.Equal(50, _service.CalculatePerformanceScore(6, 50, 50, 50));
        }

        [Fact]
        public void CalculatePerformanceScore_OutOfRangeInputs_AreClamped()
        {
            // route 150->100, items -20->0, coins 200->100
            // 15 + 40 + 0 + 20 = 75
            Assert.Equal(75, _service.CalculatePerformanceScore(1, 150, -20, 200));
        }

        [Fact]
        public void CalculatePerformanceScore_InvalidPosition_Throws()
        {
            Assert.Throws<ArgumentOutOfRangeException>(
                () => _service.CalculatePerformanceScore(0, 50, 50, 50));
        }

        // ---------- ClassifyPerformance ----------

        [Theory]
        [InlineData(100, "Elite")]
        [InlineData(90, "Elite")]
        [InlineData(89, "Great")]
        [InlineData(80, "Great")]
        [InlineData(79, "Good")]
        [InlineData(70, "Good")]
        [InlineData(69, "Average")]
        [InlineData(60, "Average")]
        [InlineData(59, "Below Average")]
        [InlineData(50, "Below Average")]
        [InlineData(49, "Poor")]
        [InlineData(0, "Poor")]
        public void ClassifyPerformance_ReturnsCorrectLabel(int score, string expected)
        {
            Assert.Equal(expected, _service.ClassifyPerformance(score));
        }

        // ---------- Score + classify together ----------

        [Fact]
        public void ScoreAndClassify_PerfectRace_IsElite()
        {
            int score = _service.CalculatePerformanceScore(1, 100, 100, 100);
            Assert.Equal("Elite", _service.ClassifyPerformance(score));
        }

        [Fact]
        public void ScoreAndClassify_MixedRace_IsGood()
        {
            int score = _service.CalculatePerformanceScore(1, 80, 60, 40);
            Assert.Equal("Good", _service.ClassifyPerformance(score));
        }
    }
}