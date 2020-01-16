package com.jd.util;

import com.google.common.collect.Lists;
import localsolver.*;

import java.io.*;
import java.util.ArrayList;
import java.util.List;

public class SantaMapLocalSolver {

    public static final Integer N_FAMILIES = 5000;

    public static final Integer N_DAYS = 100;

    public static final Integer N_CHOICE = 4;

    public static int[][] FAMILY_CHOICES = new int[N_FAMILIES][10];

    public static int[] FAMILY_SIZE = new int[N_FAMILIES + 1];

    public static LSExpression[][] x;

    public static LSExpression[] n;

    public static String FAMILY_FILE = "/Users/liuyang59/PycharmProjects/kaggle/santa_2019/family_data.in";

    public static String OUTPUT_PATH = "/Users/liuyang59/PycharmProjects/kaggle/santa_2019/";

    public static Integer SAVE_PERIOD = 60;

    public static void main(String[] args) {

        readFile(FAMILY_FILE);

        // Declares the optimization model.
        LocalSolver localsolver = new LocalSolver();
        localsolver.addCallback(LSCallbackType.TimeTicked, new LSCallback() {
            private double lastBestValue = Double.MAX_VALUE;
            private int lastBestSaveTime = 0;

            @Override
            public void callback(LocalSolver ls, LSCallbackType type) {
                assert (type == LSCallbackType.TimeTicked);
                if (ls.getSolution().getStatus().equals(LSSolutionStatus.Infeasible)) {
                    return;
                }
                LSStatistics stats = ls.getStatistics();
                LSExpression obj = ls.getModel().getObjective(0);
                if (stats.getRunningTime() - lastBestSaveTime > SAVE_PERIOD) {
                    lastBestSaveTime = writeOutput(ls.getSolution(), OUTPUT_PATH + "sol_" + obj.getDoubleValue() + ".csv");
                }
                if (obj.getDoubleValue() < lastBestValue) {
                    lastBestValue = obj.getDoubleValue();
                }

            }
        });


        LSModel model = localsolver.getModel();
        x = new LSExpression[N_FAMILIES][N_CHOICE];
        // 0-1 decisions
        for (int i = 0; i < N_FAMILIES; i++) {
            for (int d = 0; d < N_CHOICE; d++) {
                x[i][d] = model.boolVar();
            }
        }

        n = new LSExpression[N_DAYS + 1];
        for (int d = 0; d < N_DAYS; d++) {
            n[d] = model.sum();
            for (int i = 0; i < N_FAMILIES; i++) {
                for (int c = 0; c < N_CHOICE; c++) {
                    if (FAMILY_CHOICES[i][c] == d) {
                        n[d].addOperand(model.prod(x[i][c], FAMILY_SIZE[i]));
                    }
                }
            }
        }
        n[100] = n[99];

        LSExpression[] x_d = new LSExpression[N_FAMILIES];
        for (int i = 0; i < N_FAMILIES; i++) {
            x_d[i] = model.sum();
            for (int d = 0; d < N_CHOICE; d++) {
                x_d[i].addOperand(x[i][d]);
            }
            model.constraint(model.eq(1, x_d[i]));
        }

        for (int d = 0; d < N_DAYS; d++) {
            model.constraint(model.geq(n[d], 125));
            model.constraint(model.leq(n[d], 300));
        }
        model.constraint(model.eq(n[100], n[99]));

//        LSExpression[] other_choice = new LSExpression[N_FAMILIES];
        LSExpression[] pref_cost = new LSExpression[N_FAMILIES];

        for (int i = 0; i < N_FAMILIES; i++) {
//            other_choice[i] = model.sum();
//            for (int d = 0; d < N_DAYS; d++) {
//                if (!collectionContains(FAMILY_CHOICES[i], d)) {
//                    other_choice[i].addOperand(x[i][d]);
//                }
//            }
            pref_cost[i] = model.sum(model.prod(0, x[i][0])
                    , model.prod(x[i][1], 50)
                    , model.prod(x[i][2], 50 + 9 * FAMILY_SIZE[i])
                    , model.prod(x[i][3], 100 + 9 * FAMILY_SIZE[i])
            );
        }

        LSExpression pref_costs = model.sum();
        for (int i = 0; i < N_FAMILIES; i++) {
            pref_costs.addOperand(pref_cost[i]);
        }
        LSExpression accounting_penalty = model.sum();
        for (int d = 0; d < N_DAYS; d++) {
            accounting_penalty.addOperand(model.prod(model.div(model.sub(n[d], 125), 400.0),
                    model.pow(n[d], model.sum(0.5, model.div(model.abs(model.sub(n[d], n[d + 1])), 50.0)))));
        }

        //model.constraint(model.eq(pref_costs, 62868.000000));
        //model.constraint(model.eq(accounting_penalty, 6020.043432));
        //model.constraint(model.eq(n[99],125));
        //model.constraint(model.eq(n[98],125));
        //model.constraint(model.eq(n[0],300));

        //List<Integer> maxDays = Lists.newArrayList(0,16,24,3,9,18,31);
        //for(Integer maxDay : maxDays){
        //    model.constraint(model.eq(n[maxDay],300));
        //}

        model.minimize(model.sum(pref_costs, accounting_penalty));

        // close model, then solve
        model.close();
        LSSolution solution = localsolver.getSolution();
        //List<Integer> smallDays = Lists.newArrayList(33, 34, 35, 36, 40, 43, 49, 54, 55, 56, 61, 62, 63, 64, 68, 69, 70, 71, 75, 76, 77, 78, 82, 83, 84, 85, 89, 90, 91, 92, 96, 97, 98, 99);
        //for (Integer small : smallDays) {
        //    for (int i = 0; i < N_FAMILIES; i++) {
        //        if (FAMILY_CHOICES[i][0] == small) {
        //            for (int d = 0; d < N_CHOICE; d++) {
        //                solution.setIntValue(x[i][d], 1);
        //            }
        //           solution.setIntValue(x[i][0], 1);
        //        }
        //    }
        //}


        // Parameterizes the solver.
//        localsolver.getParam().setTimeLimit(10);
        localsolver.getParam().setNbThreads(8);
        localsolver.getParam().setTimeBetweenDisplays(60);
        localsolver.solve();

        writeOutput(localsolver.getSolution(), OUTPUT_PATH + "sol_" + localsolver.getModel().getObjective(0).getDoubleValue() + ".csv");
    }

    private static int writeOutput(LSSolution solution, String fileName) {
        File file = new File(fileName);
        if (!file.exists()) {
            try {
                file.createNewFile();
            } catch (IOException e) {
                e.printStackTrace();
            }
        } else {
            return solution.getLocalSolver().getStatistics().getRunningTime();
        }
        try (FileOutputStream fop = new FileOutputStream(file)) {

            List<Integer> result = new ArrayList();
            for (int i = 0; i < N_FAMILIES; i++) {
                for (int d = 0; d < N_CHOICE; d++) {
                    if (solution.getIntValue(x[i][d]) == 1) {
                        result.add(FAMILY_CHOICES[i][d] + 1);
                    }
                }
            }
            fop.write("family_id,assigned_day\n".getBytes());
            Integer family_num = 0;
            for (Integer day : result) {
                fop.write(family_num.toString().getBytes());
                fop.write(",".getBytes());
                fop.write(day.toString().getBytes());
                fop.write("\n".getBytes());
                family_num++;
            }
            fop.flush();
            fop.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
        System.out.println(fileName + " save done.");
        return solution.getLocalSolver().getStatistics().getRunningTime();
    }

    private static void readFile(String fileName) {

        try {
            File file = new File(fileName);
            BufferedReader bufferedReader = new BufferedReader(new FileReader(file));
            String strLine = null;
            int lineCount = 0;
            while (null != (strLine = bufferedReader.readLine())) {
                String[] lineStrs = strLine.split("\t");
                for (int i = 0; i < 10; i++) {
                    FAMILY_CHOICES[lineCount][i] = Integer.parseInt(lineStrs[i + 1]) - 1;

                }
                FAMILY_SIZE[lineCount] = Integer.parseInt(lineStrs[11]);
                lineCount++;
            }
        } catch (Exception e) {
            e.printStackTrace();
        }


    }

    private static boolean collectionContains(int[] collection, int val) {
        for (int i = 0; i < collection.length; i++) {
            if (collection[i] == val) {
                return true;
            }
        }
        return false;
    }
}
