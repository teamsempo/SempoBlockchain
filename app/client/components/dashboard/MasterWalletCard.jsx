// Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
// The code in this file is not included in the GPL license applied to this repository
// Unauthorized copying of this file, via any medium is strictly prohibited

import React from "react";
import { connect } from "react-redux";
import styled from "styled-components";
import { Card, Typography } from "antd";
import { LinkOutlined } from "@ant-design/icons";
import { HorizontalBar } from "react-chartjs-2";
import { formatMoney, getActiveToken } from "../../utils";

const { Text } = Typography;

const mapStateToProps = state => {
  return {
    creditTransferStats: state.metrics.metricsState,
    activeToken: getActiveToken(state)
  };
};

class MasterWalletCard extends React.Component {
  constructor() {
    super();
    this.state = {};
  }

  render() {
    const { creditTransferStats, activeToken } = this.props;
    const masterWalletBalance = creditTransferStats.master_wallet_balance / 100;
    const amountDisbursed = creditTransferStats.total_distributed / 100;
    const amountWithdrawn = creditTransferStats.total_withdrawn / 100;
    const amountReclaimed = creditTransferStats.total_reclaimed / 100;
    const symbol = activeToken && activeToken.symbol;

    const amountInCirculation =
      amountDisbursed - amountWithdrawn - amountReclaimed;

    console.log("Master wallet balance is", masterWalletBalance);

    const tracker_link = `${window.ETH_EXPLORER_URL}/address/${window.master_wallet_address}`;

    var options = {
      animation: false,
      maintainAspectRatio: false,
      legend: {
        display: false
      },
      tooltips: {
        enabled: false,
        mode: "nearest",
        backgroundColor: "rgba(87, 97, 113, 0.9)",
        cornerRadius: 1
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
              max:
                Math.abs(masterWalletBalance) +
                amountInCirculation +
                amountWithdrawn
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

    let data;

    if (masterWalletBalance >= 0) {
      data = {
        datasets: [
          {
            barPercentage: 1,
            label: `Current Balance`,
            backgroundColor: ["#A7D6D7"],
            data: [masterWalletBalance]
          },
          {
            barPercentage: 1,
            label: `Amount in Circulation`,
            backgroundColor: ["#EDCBA2"],
            data: [amountInCirculation]
          },
          {
            barPercentage: 1,
            label: `Amount Withdrawn`,
            backgroundColor: ["#AF6FC1"],
            data: [amountWithdrawn]
          }
        ]
      };
    } else {
      data = {
        datasets: [
          {
            barPercentage: 1,
            label: `Current Balance`,
            backgroundColor: ["#d76665"],
            data: [-masterWalletBalance]
          },
          {
            barPercentage: 1,
            label: `Amount in Circulation`,
            backgroundColor: ["#EDCBA2"],
            data: [amountInCirculation]
          },
          {
            barPercentage: 1,
            label: `Amount Withdrawn`,
            backgroundColor: ["#AF6FC1"],
            data: [amountWithdrawn]
          }
        ]
      };
    }

    return (
      <Card
        title="Master Wallet"
        bordered={false}
        bodyStyle={{ height: "140px" }}
        style={{ width: "100%" }}
        extra={
          <a href={tracker_link} target="_blank">
            <LinkOutlined /> View in Explorer
          </a>
        }
      >
        <div style={{ height: "100%", width: "100%" }}>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <Wrapper>
              <Text type="secondary" strong={true}>
                {formatMoney(
                  masterWalletBalance,
                  0,
                  undefined,
                  undefined,
                  symbol
                )}
              </Text>
              <Text
                type="secondary"
                strong={true}
                style={{
                  color: masterWalletBalance > 0 ? "#A7D6D7" : "#d76665"
                }}
              >
                Current Balance
              </Text>
            </Wrapper>
            <Wrapper>
              <Text type="secondary" strong={true}>
                {formatMoney(
                  amountInCirculation,
                  0,
                  undefined,
                  undefined,
                  symbol
                )}
              </Text>
              <Text type="secondary" strong={true} style={{ color: "#EDCBA2" }}>
                In Circulation
              </Text>
            </Wrapper>
            <Wrapper>
              <Text type="secondary" strong={true}>
                {formatMoney(amountWithdrawn, 0, undefined, undefined, symbol)}
              </Text>
              <Text type="secondary" strong={true} style={{ color: "#AF6FC1" }}>
                Withdrawn
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
