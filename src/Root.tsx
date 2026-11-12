import React from "react";
import { Composition } from "remotion";
import { BridgeShort, BRIDGE_FRAMES } from "./videos/bridge/Bridge";
import { DancingPlague, DANCING_FRAMES } from "./videos/dancing/Dancing";
import { MolassesFlood, MOLASSES_FRAMES } from "./videos/molasses/Molasses";

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="BridgeShort"
        component={BridgeShort}
        durationInFrames={BRIDGE_FRAMES}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="DancingPlague"
        component={DancingPlague}
        durationInFrames={DANCING_FRAMES}
        fps={30}
        width={1440}
        height={2560}
      />
      <Composition
        id="MolassesFlood"
        component={MolassesFlood}
        durationInFrames={MOLASSES_FRAMES}
        fps={30}
        width={1440}
        height={2560}
      />
    </>
  );
};
