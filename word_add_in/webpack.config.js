const HtmlWebpackPlugin = require("html-webpack-plugin");
const CopyWebpackPlugin = require("copy-webpack-plugin");
const path = require("path");

module.exports = (env, options) => {
  const dev = options.mode === "development";
  
  return {
    devtool: dev ? "source-map" : false,
    entry: {
      taskpane: "./src/index.js",
      commands: "./src/commands/commands.js"
    },
    output: {
      path: path.resolve(__dirname, "dist"),
      filename: "[name].js",
      clean: true,
    },
    module: {
      rules: [
        {
          test: /\.js$/,
          exclude: /node_modules/,
          use: {
            loader: "babel-loader",
            options: {
              presets: ["@babel/preset-env"]
            }
          }
        },
        {
          test: /\.css$/,
          use: ["style-loader", "css-loader"]
        },
        {
          test: /\.html$/,
          use: "html-loader"
        }
      ]
    },
    plugins: [
      new HtmlWebpackPlugin({
        filename: "taskpane.html",
        template: "./src/taskpane/taskpane.html",
        chunks: ["taskpane"]
      }),
      new HtmlWebpackPlugin({
        filename: "commands.html",
        template: "./src/commands/commands.html",
        chunks: ["commands"]
      }),
      new CopyWebpackPlugin({
        patterns: [
          { from: "manifest.xml", to: "." },
          { from: "assets", to: "assets", noErrorOnMissing: true }
        ]
      })
    ],
    devServer: {
      server: {
        type: "https",
      },
      static: {
        directory: path.join(__dirname, "dist"),
      },
      port: process.env.npm_package_config_dev_server_port || 3000,
      hot: true,
      headers: {
        "Access-Control-Allow-Origin": "*"
      }
    }
  };
};
