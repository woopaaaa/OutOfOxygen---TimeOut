import type { PlanResult } from "./types"; //take the label with data type "PlanResult" that was exported from from types.ts

import exampleJson from "@/data/output-example.json"; //import the out-put example json
export const plan = exampleJson as PlanResult; //eveeytime plan is used, the data from exampleJson is the datatype from PlanResult,it will be determined

