export const reduxState = {
  metricsState: {
    transfer_stats: {
      count: {
        total: 6,
        groups: {
          cheese: 3,
          milk: 5,
          bananas: 6,
          mushrooms: 11,
          apples: 3
        },
        time_series: {
          cheese: [
            { date: "2020-07-23T00:00:00", value: 1 },
            { date: "2020-07-24T00:00:00", value: 2 },
            { date: "2020-07-25T00:00:00", value: 4 }
          ],
          milk: [
            { date: "2020-07-23T00:00:00", value: 3 },
            { date: "2020-07-24T00:00:00", value: 2 },
            { date: "2020-07-25T00:00:00", value: 2 }
          ],
          bananas: [
            { date: "2020-07-23T00:00:00", value: 5 },
            { date: "2020-07-24T00:00:00", value: 1 },
            { date: "2020-07-25T00:00:00", value: 3 }
          ],
          mushrooms: [
            { date: "2020-07-23T00:00:00", value: 1 },
            { date: "2020-07-24T00:00:00", value: 3 },
            { date: "2020-07-25T00:00:00", value: 6 }
          ],
          apples: [
            { date: "2020-07-23T00:00:00", value: 1 },
            { date: "2020-07-24T00:00:00", value: 0 },
            { date: "2020-07-25T00:00:00", value: 2 }
          ]
        }
      },
      volume: {
        total: 2000,
        groups: {
          cheese: 1200,
          milk: 2000
        },
        time_series: {
          cheese: [
            { date: "2020-07-23T00:00:00", value: 550 },
            { date: "2020-07-24T00:00:00", value: 900 },
            { date: "2020-07-25T00:00:00", value: 123 }
          ],
          milk: [
            { date: "2020-07-23T00:00:00", value: 650 },
            { date: "2020-07-24T00:00:00", value: 1100 },
            { date: "2020-07-25T00:00:00", value: 111 }
          ]
        }
      },
      average_volume: {
        total: 300,
        groups: {
          cheese: 1100,
          milk: 2000
        },
        time_series: {
          cheese: [
            { date: "2020-07-23T00:00:00", value: 500 },
            { date: "2020-07-24T00:00:00", value: 1000 }
          ],
          milk: [
            { date: "2020-07-23T00:00:00", value: 600 },
            { date: "2020-07-24T00:00:00", value: 1000 }
          ]
        }
      },
      average_count: {
        total: 6,
        groups: {
          cheese: 3,
          milk: 5
        },
        time_series: {
          cheese: [
            { date: "2020-07-23T00:00:00", value: 1 },
            { date: "2020-07-24T00:00:00", value: 2 }
          ],
          milk: [
            { date: "2020-07-23T00:00:00", value: 3 },
            { date: "2020-07-24T00:00:00", value: 2 }
          ]
        }
      },
      allowed_groupbys: ["stonks", "gender"],
      selected_groupby: "stonks",
      selected_time_series: "volume"
    }
  }
};
