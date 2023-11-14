import { Trigger } from "@radix-ui/react-tabs";

import { ApiTab } from "../types";

type BrainDefinitionTabTriggerProps = {
  label: string;
  value: ApiTab;
  selected: boolean;
  onChange: (value: ApiTab) => unknown;
};

export const BrainDefinitionTabTrigger = ({
  label,
  value,
  selected,
  onChange,
}: BrainDefinitionTabTriggerProps): JSX.Element => {
  return (
    <Trigger
      className={`flex-1 pb-4 border-gray-500 text-md align-center mb-3 ${
        selected ? "font-medium border-b-2" : ""
      }`}
      value={value}
      onClick={() => onChange(value)}
    >
      {label}
    </Trigger>
  );
};
