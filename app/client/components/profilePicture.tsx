import React from "react";
import styled from "styled-components";

export default function ProfilePicture({roll, sublabel, label, url}){
  if (roll) {
    var quantised_roll = Math.floor(roll / 90 + 0.5) * -90;
  } else {
    quantised_roll = 0;
  }

  if (sublabel) {
    var sublabel = (
      <SublabelContainer>
        <Label style={{ padding: "0.2em" }}>{sublabel}</Label>
      </SublabelContainer>
    );
  } else {
    sublabel = null;
  }

  return (
    <div style={{ margin: "1em 0" }}>
      <Label> {label} </Label>
      <div
        style={{
          backgroundImage: `url(${url})`,
          backgroundSize: "cover",
          backgroundRepeat: "no-repeat",
          backgroundPosition: "center center",
          transform: `rotate(${quantised_roll}deg)`,
          width: "150px",
          height: "150px",
          marginTop: "0.5em"
        }}
      >
        <div
          style={{
            transform: `rotate(${-quantised_roll}deg)`,
            width: "100%",
            height: "100%"
          }}
        >
          {sublabel}
        </div>
      </div>
    </div>
  );
}

const Label = styled.div`
  font-size: 15px;
  font-weight: 600;
`;

const SublabelContainer = styled.div`
  position: absolute;
  bottom: 0;
  color: white;
  background-color: #2b333bab;
  width: 100%;
  text-align: center;
`;
