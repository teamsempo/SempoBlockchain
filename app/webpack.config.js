var webpack = require("webpack");
const path = require("path");
const fs = require("fs");
const APP_DIR = path.resolve(__dirname, "client");
const BUILD_DIR = path.resolve(__dirname, "server/static/javascript/dist");
const CleanWebpackPlugin = require("clean-webpack-plugin");
const BundleAnalyzerPlugin =
  require("webpack-bundle-analyzer").BundleAnalyzerPlugin;
const MomentLocalesPlugin = require("moment-locales-webpack-plugin");
const TerserPlugin = require("terser-webpack-plugin");

const lessToJs = require("less-vars-to-js");
const themeVariables = lessToJs(
  fs.readFileSync(path.join(__dirname, "client/ant-theme-vars.less"), "utf8")
);
const tsImportPluginFactory = require("ts-import-plugin");

module.exports = function (env, argv) {
  return {
    entry: APP_DIR + "/index.jsx",
    plugins: [
      new CleanWebpackPlugin([BUILD_DIR]),

      new MomentLocalesPlugin({
        localesToKeep: ["es-us"],
      }),

      new BundleAnalyzerPlugin({
        analyzerMode: "disabled",
        generateStatsFile: true,
        statsOptions: { source: false },
      }),
    ],
    output: {
      path: BUILD_DIR,
      publicPath: "/static/javascript/dist/",
      // chunkFilename: '[name].bundle.[contenthash].js',
      filename: "[name].bundle.[contenthash].js",
    },

    devtool: argv.mode === "production" ? "source-map" : "inline-source-map",
    resolve: {
      extensions: [".ts", ".tsx", ".js", ".jsx", ".json", ".css", ".less"],
    },
    module: {
      rules: [
        {
          test: /\.css$/,
          use: [
            { loader: "style-loader" },
            { loader: "css-modules-typescript-loader" },
            {
              loader: "css-loader",
              options: {
                importLoaders: 1,
                modules: true,
              },
            },
          ],
          include: /\.module\.css$/,
        },
        {
          test: /\.css$/,
          use: ["style-loader", "css-loader"],
          exclude: /\.module\.css$/,
        },
        {
          test: /\.(js|jsx)$/,
          exclude: /node_modules/,
          include: APP_DIR,

          use: [
            {
              loader: "babel-loader",
              options: {
                babelrc: false,
                presets: ["env", "react", "stage-2"],
                plugins: [["import", { libraryName: "antd", style: true }]],
              },
            },
          ],
        },
        {
          test: /\.(ts|tsx)?$/,
          exclude: /node_modules/,
          loader: "ts-loader",
          options: {
            transpileOnly: true,
            getCustomTransformers: () => ({
              before: [
                tsImportPluginFactory([
                  {
                    libraryName: "antd",
                    libraryDirectory: "lib",
                    style: true,
                  },
                ]),
              ],
            }),
          },
        },
        {
          test: /\.less$/,
          use: [
            { loader: "style-loader" },
            { loader: "css-loader" },
            {
              loader: "less-loader",
              options: {
                lessOptions: {
                  modifyVars: themeVariables,
                  javascriptEnabled: true,
                },
              },
            },
          ],
        },
      ],
    },
    optimization: {
      splitChunks: {
        chunks: "all",
      },
      minimize: argv.mode === "production" ? true : false,
      minimizer: [new TerserPlugin()],
    },
  };
};
