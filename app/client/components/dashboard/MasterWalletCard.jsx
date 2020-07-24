import React from "react";
import { connect } from "react-redux";
import styled from "styled-components";
import { Card, Typography } from "antd";
import { HorizontalBar } from "react-chartjs-2";
import { formatMoney } from "../../utils";

const { Text } = Typography;

const mapStateToProps = state => {
  return {
    creditTransferStats: state.metrics.metricsState,
    activeOrganisation: state.organisations.byId[state.login.organisationId]
  };
};

class MasterWalletCard extends React.Component {
  constructor() {
    super();
    this.state = {};
  }

  render() {
    const { creditTransferStats, activeOrganisation } = this.props;
    const masterWalletBalance = creditTransferStats.master_wallet_balance / 100;
    const amountDisbursed = creditTransferStats.total_distributed / 100;
    const symbol = activeOrganisation.token.symbol;

    var options = {
      animation: false,
      maintainAspectRatio: false,
      legend: {
        display: false
      },
      tooltips: {
        mode: "nearest",
        backgroundColor: "rgba(87, 97, 113, 0.9)"
      },

      scales: {
        xAxes: [
          {
            gridLines: {
              display: false
            },
            ticks: {
              beginAtZero: true,
              min: 0,
              max: masterWalletBalance + amountDisbursed
            },
            stacked: true,
            display: false,
            offset: false
          }
        ],
        yAxes: [
          {
            gridLines: {
              display: false
            },
            ticks: {
              beginAtZero: true,
              min: 0
            },
            stacked: true,
            display: false
          }
        ]
      }
    };

    var data = {
      datasets: [
        {
          barPercentage: 1,
          label: `Current Balance`,
          backgroundColor: ["#A7D6D7"],
          data: [masterWalletBalance]
        },
        {
          barPercentage: 1,
          label: `Amount Disbursed`,
          backgroundColor: ["#EDCBA2"],
          data: [amountDisbursed]
        }
      ]
    };
    return (
      <Card
        title="Master Wallet"
        bordered={false}
        bodyStyle={{ height: "140px" }}
      >
        <div style={{ height: "100%", width: "100%" }}>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <Wrapper>
              <Text type="secondary">
                {formatMoney(
                  masterWalletBalance,
                  0,
                  undefined,
                  undefined,
                  symbol
                )}
              </Text>
              <Text type="secondary" strong={true} style={{ color: "#A7D6D7" }}>
                Current Balance
              </Text>
            </Wrapper>
            <Wrapper>
              <Text type="secondary">
                {formatMoney(amountDisbursed, 0, undefined, undefined, symbol)}
              </Text>
              <Text type="secondary" strong={true} style={{ color: "#EDCBA2" }}>
                Amount Disbursed
              </Text>
            </Wrapper>
          </div>
          <div style={{ height: 40, width: "100%" }}>
            <HorizontalBar data={data} options={options} />
          </div>
        </div>
      </Card>
    );
  }
}

export default connect(
  mapStateToProps,
  null
)(MasterWalletCard);

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
`;
