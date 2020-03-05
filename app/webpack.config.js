var webpack = require("webpack");

const path = require("path");
const APP_DIR = path.resolve(__dirname, "client");
const BUILD_DIR = path.resolve(__dirname, "server/static/javascript/dist");
const CleanWebpackPlugin = require("clean-webpack-plugin");
const CompressionPlugin = require("compression-webpack-plugin");
const BundleAnalyzerPlugin = require("webpack-bundle-analyzer")
  .BundleAnalyzerPlugin;
const MomentLocalesPlugin = require("moment-locales-webpack-plugin");

module.exports = {
  entry: APP_DIR + "/index.jsx",
  plugins: [
    new CleanWebpackPlugin([BUILD_DIR]),
    // new CompressionPlugin()

    new MomentLocalesPlugin({
      localesToKeep: ["es-us"]
    }),

    new BundleAnalyzerPlugin({
      analyzerMode: "disabled",
      generateStatsFile: true,
      statsOptions: { source: false }
    })
  ],
  output: {
    path: BUILD_DIR,
    publicPath: "/static/javascript/dist/",
    // chunkFilename: '[name].bundle.[contenthash].js',
    filename: "[name].bundle.[contenthash].js"
  },
  devtool: "#cheap-module-source-map.", // #eval-source-map" #cheap-module-source-map."
  resolve: {
    extensions: [".ts", ".tsx", ".js", ".jsx", ".json", ".css"]
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
              modules: true
            }
          }
        ],
        include: /\.module\.css$/
      },
      {
        test: /\.css$/,
        use: ["style-loader", "css-loader"],
        exclude: /\.module\.css$/
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
              presets: ["env", "react", "stage-2"]
            }
          }
        ]
      },
      {
        test: /\.(ts|tsx)?$/,
        exclude: /node_modules/,
        loader: "awesome-typescript-loader"
      }
    ]
  }
};
