module.exports = [
(()=>{"use strict";return[
"[project]/app/favicon.ico.mjs { IMAGE => \"[project]/app/favicon.ico (static in ecmascript, tag client)\" } [app-rsc] (structured image object, ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>__TURBOPACK__default__export__
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$app$2f$favicon$2e$ico__$28$static__in__ecmascript$2c$__tag__client$29$__ = __turbopack_context__.i("[project]/app/favicon.ico (static in ecmascript, tag client)");
;
const __TURBOPACK__default__export__ = {
    src: __TURBOPACK__imported__module__$5b$project$5d2f$app$2f$favicon$2e$ico__$28$static__in__ecmascript$2c$__tag__client$29$__["default"],
    width: 48,
    height: 48
};
}),
"[project]/app/page.tsx [app-rsc] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>DashboardPage
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/rsc/react-jsx-dev-runtime.js [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$planData$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/lib/planData.ts [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$StatCard$2e$tsx__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/StatCard.tsx [app-rsc] (ecmascript)");
;
;
;
async function DashboardPage() {
    const plan = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$planData$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["getPlan"])();
    const metrics = plan.metrics.optimised;
    const ordersAtRisk = metrics.orders_late + metrics.orders_infeasible; //add the late orders with the one cannot be made
    const shortMaterials = plan.material_requirements.filter((m)=>m.shortage > 0).length;
    const utilisationPercent = Math.round(metrics.utilisation * 100);
    const shortNames = plan.material_requirements.filter((m)=>m.shortage > 0).map((m)=>m.name).join(", ");
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("h1", {
                className: "text-2xl font-bold",
                children: "Factory's Health Dashboard"
            }, void 0, false, {
                fileName: "[project]/app/page.tsx",
                lineNumber: 16,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                className: "mt-1 text-slate-600",
                children: "A quick overview of orders, stock, capacity and costs."
            }, void 0, false, {
                fileName: "[project]/app/page.tsx",
                lineNumber: 17,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$StatCard$2e$tsx__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["default"], {
                        label: "Total orders",
                        value: metrics.orders_total
                    }, void 0, false, {
                        fileName: "[project]/app/page.tsx",
                        lineNumber: 20,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$StatCard$2e$tsx__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["default"], {
                        label: "Orders at risk",
                        value: ordersAtRisk,
                        note: " are late or cannot be made"
                    }, void 0, false, {
                        fileName: "[project]/app/page.tsx",
                        lineNumber: 21,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$StatCard$2e$tsx__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["default"], {
                        label: "Materials stock low",
                        value: shortMaterials,
                        note: `${shortNames} (out of ${plan.material_requirements.length})`
                    }, void 0, false, {
                        fileName: "[project]/app/page.tsx",
                        lineNumber: 22,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$StatCard$2e$tsx__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["default"], {
                        label: "Capacity used",
                        value: `${utilisationPercent}%`,
                        note: `${metrics.hours_used} of ${metrics.hours_available} hours`
                    }, void 0, false, {
                        fileName: "[project]/app/page.tsx",
                        lineNumber: 23,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/app/page.tsx",
                lineNumber: 19,
                columnNumber: 7
            }, this),
            plan.warnings.length > 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "mt-6 rounded-lg border border-red-200 bg-red-50 p-5",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                        className: "font-semibold text-red-800",
                        children: "Needs attention"
                    }, void 0, false, {
                        fileName: "[project]/app/page.tsx",
                        lineNumber: 27,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("ul", {
                        className: "mt-3 list-disc pl-5 text-sm text-red-700",
                        children: plan.warnings.map((warning)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("li", {
                                children: warning
                            }, warning, false, {
                                fileName: "[project]/app/page.tsx",
                                lineNumber: 30,
                                columnNumber: 10
                            }, this))
                    }, void 0, false, {
                        fileName: "[project]/app/page.tsx",
                        lineNumber: 28,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/app/page.tsx",
                lineNumber: 26,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/app/page.tsx",
        lineNumber: 15,
        columnNumber: 5
    }, this);
}
}),
"[project]/components/StatCard.tsx [app-rsc] (ecmascript)", ((__turbopack_context__) => {
"use strict";

// for the cards
__turbopack_context__.s([
    "default",
    ()=>StatCard
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/rsc/react-jsx-dev-runtime.js [app-rsc] (ecmascript)");
;
function StatCard({ label, value, note }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "rounded-lg border border-slate-200 bg-white p-5",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                className: "text-sm text-slate-500",
                children: label
            }, void 0, false, {
                fileName: "[project]/components/StatCard.tsx",
                lineNumber: 12,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                className: "mt-2 text-3xl font-bold",
                children: value
            }, void 0, false, {
                fileName: "[project]/components/StatCard.tsx",
                lineNumber: 13,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                className: "mt-1 text-sm text-slate-500",
                children: note
            }, void 0, false, {
                fileName: "[project]/components/StatCard.tsx",
                lineNumber: 14,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/components/StatCard.tsx",
        lineNumber: 11,
        columnNumber: 5
    }, this);
}
}),
"[project]/lib/planData.ts [app-rsc] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "getPlan",
    ()=>getPlan
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$data$2f$output$2d$example$2e$json$2e5b$json$5d2e$cjs__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/data/output-example.json.[json].cjs [app-rsc] (ecmascript)");
;
const API_URL = "http://localhost:8000/plan/current";
async function getPlan() {
    try {
        const response = await fetch(API_URL); //visit api, wait for answer and save answer in response
        if (!response.ok) {
            throw new Error(`API answered ${response.status}`);
        }
        const answer = await response.json();
        return answer.plan;
    } catch (error) {
        console.warn("Backend not reachable, using example data instead:", error);
        return __TURBOPACK__imported__module__$5b$project$5d2f$data$2f$output$2d$example$2e$json$2e5b$json$5d2e$cjs__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["default"];
    }
}
}),
]})(),
"[externals]/next/dist/server/app-render/module-loading/track-module-loading.external.js [external] (next/dist/server/app-render/module-loading/track-module-loading.external.js, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("next/dist/server/app-render/module-loading/track-module-loading.external.js", () => require("next/dist/server/app-render/module-loading/track-module-loading.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/shared/lib/no-fallback-error.external.js [external] (next/dist/shared/lib/no-fallback-error.external.js, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("next/dist/shared/lib/no-fallback-error.external.js", () => require("next/dist/shared/lib/no-fallback-error.external.js"));

module.exports = mod;
}),
"[project]/app/favicon.ico (static in ecmascript, tag client)", ((__turbopack_context__) => {

__turbopack_context__.v("/_next/static/media/favicon.117ezoe8m31dk.ico" + (globalThis["NEXT_CLIENT_ASSET_SUFFIX"] || ''));}),
"[project]/app/page.tsx [app-rsc] (ecmascript, Next.js Server Component)", (function(__turbopack_context__){

__turbopack_context__.n(__turbopack_context__.i("[project]/app/page.tsx [app-rsc] (ecmascript)"));
}),
"[project]/data/output-example.json.[json].cjs [app-rsc] (ecmascript)", ((__turbopack_context__, module, exports) => {

module.exports = {
    "_note": "EXAMPLE of the response shape, calculated from the illustrative sample data in data/. Not real business data.",
    "generated_at": "2026-10-22T20:00:00+08:00",
    "planning_start": "2026-10-21",
    "schedule": [
        {
            "order_id": "ORD-002",
            "customer": "Hotel Seri Melati",
            "product_id": "CURRY_PUFF",
            "quantity": 40,
            "due_date": "2026-10-22",
            "status": "on_time",
            "start_hour": 0.0,
            "end_hour": 1.6,
            "material_cost_rm": 267.0,
            "reason": "Enough materials and finishes before the deadline"
        },
        {
            "order_id": "ORD-001",
            "customer": "Kedai Runcit Ah Seng",
            "product_id": "COOKIE_BTR",
            "quantity": 60,
            "due_date": "2026-10-23",
            "status": "on_time",
            "start_hour": 1.6,
            "end_hour": 3.1,
            "material_cost_rm": 394.05,
            "reason": "Enough materials and finishes before the deadline"
        },
        {
            "order_id": "ORD-005",
            "customer": "Sekolah Kebangsaan Taman Jaya",
            "product_id": "CURRY_PUFF",
            "quantity": 60,
            "due_date": "2026-10-23",
            "status": "infeasible",
            "start_hour": null,
            "end_hour": null,
            "material_cost_rm": 0,
            "reason": "Not enough Chicken meat (short 10 kg)"
        },
        {
            "order_id": "ORD-003",
            "customer": "Pasar Mini Fatimah",
            "product_id": "KUIH_KELAPA",
            "quantity": 80,
            "due_date": "2026-10-24",
            "status": "on_time",
            "start_hour": 3.1,
            "end_hour": 5.39,
            "material_cost_rm": 282.4,
            "reason": "Enough materials and finishes before the deadline"
        },
        {
            "order_id": "ORD-004",
            "customer": "Kafe Bukit Bintang",
            "product_id": "COOKIE_BTR",
            "quantity": 100,
            "due_date": "2026-10-26",
            "status": "infeasible",
            "start_hour": null,
            "end_hour": null,
            "material_cost_rm": 0,
            "reason": "Not enough Butter (short 4.2 kg), Eggs (short 140 pcs)"
        },
        {
            "order_id": "ORD-006",
            "customer": "Raya Hamper Co",
            "product_id": "KUIH_KELAPA",
            "quantity": 120,
            "due_date": "2026-10-27",
            "status": "infeasible",
            "start_hour": null,
            "end_hour": null,
            "material_cost_rm": 0,
            "reason": "Not enough Refined sugar (short 9 kg), Grated coconut (short 10 kg), Eggs (short 60 pcs)"
        }
    ],
    "material_requirements": [
        {
            "material_id": "BUTTER",
            "name": "Butter",
            "unit": "kg",
            "required": 19.2,
            "in_stock": 15.0,
            "shortage": 4.2,
            "purchase_quantity": 9.2,
            "unit_cost_rm": 28.0,
            "purchase_cost_rm": 257.6,
            "lead_time_days": 4
        },
        {
            "material_id": "CHICKEN",
            "name": "Chicken meat",
            "unit": "kg",
            "required": 35.0,
            "in_stock": 25.0,
            "shortage": 10.0,
            "purchase_quantity": 15.0,
            "unit_cost_rm": 11.5,
            "purchase_cost_rm": 172.5,
            "lead_time_days": 2
        },
        {
            "material_id": "COCONUT",
            "name": "Grated coconut",
            "unit": "kg",
            "required": 20.0,
            "in_stock": 10.0,
            "shortage": 10.0,
            "purchase_quantity": 12.0,
            "unit_cost_rm": 9.5,
            "purchase_cost_rm": 114.0,
            "lead_time_days": 1
        },
        {
            "material_id": "EGG",
            "name": "Eggs",
            "unit": "pcs",
            "required": 620.0,
            "in_stock": 300.0,
            "shortage": 320.0,
            "purchase_quantity": 380.0,
            "unit_cost_rm": 0.45,
            "purchase_cost_rm": 171.0,
            "lead_time_days": 1
        },
        {
            "material_id": "FLOUR",
            "name": "Wheat flour",
            "unit": "kg",
            "required": 174.0,
            "in_stock": 120.0,
            "shortage": 54.0,
            "purchase_quantity": 74.0,
            "unit_cost_rm": 3.2,
            "purchase_cost_rm": 236.8,
            "lead_time_days": 2
        },
        {
            "material_id": "PACK",
            "name": "Packaging box",
            "unit": "pcs",
            "required": 460.0,
            "in_stock": 500.0,
            "shortage": 0,
            "purchase_quantity": 60.0,
            "unit_cost_rm": 0.6,
            "purchase_cost_rm": 36.0,
            "lead_time_days": 5
        },
        {
            "material_id": "SUGAR",
            "name": "Refined sugar",
            "unit": "kg",
            "required": 64.0,
            "in_stock": 40.0,
            "shortage": 24.0,
            "purchase_quantity": 34.0,
            "unit_cost_rm": 2.85,
            "purchase_cost_rm": 96.9,
            "lead_time_days": 2
        }
    ],
    "purchase_request": {
        "status": "pending_approval",
        "requires_role": "owner",
        "lines": [
            {
                "material_id": "BUTTER",
                "name": "Butter",
                "unit": "kg",
                "quantity": 9.2,
                "unit_cost_rm": 28.0,
                "cost_rm": 257.6
            },
            {
                "material_id": "CHICKEN",
                "name": "Chicken meat",
                "unit": "kg",
                "quantity": 15.0,
                "unit_cost_rm": 11.5,
                "cost_rm": 172.5
            },
            {
                "material_id": "COCONUT",
                "name": "Grated coconut",
                "unit": "kg",
                "quantity": 12.0,
                "unit_cost_rm": 9.5,
                "cost_rm": 114.0
            },
            {
                "material_id": "EGG",
                "name": "Eggs",
                "unit": "pcs",
                "quantity": 380.0,
                "unit_cost_rm": 0.45,
                "cost_rm": 171.0
            },
            {
                "material_id": "FLOUR",
                "name": "Wheat flour",
                "unit": "kg",
                "quantity": 74.0,
                "unit_cost_rm": 3.2,
                "cost_rm": 236.8
            },
            {
                "material_id": "PACK",
                "name": "Packaging box",
                "unit": "pcs",
                "quantity": 60.0,
                "unit_cost_rm": 0.6,
                "cost_rm": 36.0
            },
            {
                "material_id": "SUGAR",
                "name": "Refined sugar",
                "unit": "kg",
                "quantity": 34.0,
                "unit_cost_rm": 2.85,
                "cost_rm": 96.9
            }
        ],
        "total_cost_rm": 1084.8
    },
    "metrics": {
        "baseline": {
            "orders_total": 6,
            "orders_on_time": 3,
            "orders_late": 0,
            "orders_infeasible": 3,
            "on_time_rate": 0.5,
            "total_material_cost_rm": 943.45,
            "hours_used": 5.39,
            "hours_available": 48.0,
            "utilisation": 0.11
        },
        "optimised": {
            "orders_total": 6,
            "orders_on_time": 3,
            "orders_late": 0,
            "orders_infeasible": 3,
            "on_time_rate": 0.5,
            "total_material_cost_rm": 943.45,
            "hours_used": 5.39,
            "hours_available": 48.0,
            "utilisation": 0.11
        }
    },
    "warnings": [
        "Order ORD-005 cannot be made: Not enough Chicken meat (short 10 kg)",
        "Order ORD-004 cannot be made: Not enough Butter (short 4.2 kg), Eggs (short 140 pcs)",
        "Order ORD-006 cannot be made: Not enough Refined sugar (short 9 kg), Grated coconut (short 10 kg), Eggs (short 60 pcs)"
    ],
    "assumptions": [
        "One production line; orders are made one after another",
        "No partial orders: an order is made in full or not at all",
        "Purchased materials are not counted as arriving within this plan"
    ]
};
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__1pv8n43g799-l._.js.map