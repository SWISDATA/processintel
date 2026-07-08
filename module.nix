{ self, ... }:
{
  config,
  lib,
  pkgs,
  ...
}:

let
  serviceName = "processintel";
  runtimeDir = "/run/${serviceName}";
  socketFile = "${runtimeDir}/socket";
  package = self.packages.${pkgs.system}.processintel;
  cacheDir = "/var/cache/${serviceName}";

  cfg = config.services.processintel;

  fontconfigFile = pkgs.writeText "fonts.conf" ''
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">
    <fontconfig>
      <description>Default configuration file</description>

      <!--
        Accept deprecated 'mono' alias, replacing it with 'monospace'
      -->
      <match target="pattern">
        <test qual="any" name="family">
          <string>mono</string>
        </test>
        <edit name="family" mode="assign" binding="same">
          <string>monospace</string>
        </edit>
      </match>

      <!--
        Accept alternate 'sans serif' spelling, replacing it with 'sans-serif'
      -->
      <match target="pattern">
        <test qual="any" name="family">
          <string>sans serif</string>
        </test>
        <edit name="family" mode="assign" binding="same">
          <string>sans-serif</string>
        </edit>
      </match>

      <!--
        Accept deprecated 'sans' alias, replacing it with 'sans-serif'
      -->
      <match target="pattern">
        <test qual="any" name="family">
          <string>sans</string>
        </test>
        <edit name="family" mode="assign" binding="same">
          <string>sans-serif</string>
        </edit>
      </match>

      <!--
        Accept alternate 'system ui' spelling, replacing it with 'system-ui'
      -->
      <match target="pattern">
        <test qual="any" name="family">
          <string>system ui</string>
        </test>
        <edit name="family" mode="assign" binding="same">
          <string>system-ui</string>
        </edit>
      </match>

      <cachedir>${cacheDir}/fontconfig</cachedir>

      <!--
        Fonts
      -->
      <dir>${pkgs.source-sans}/share/fonts</dir>
      <dir>${pkgs.montserrat}/share/fonts</dir>
    </fontconfig>
  '';

in
{
  options = {
    services.${serviceName} = {
      enable = lib.mkEnableOption ''
        Whether to enable ProcessIntel services
      '';

      production = lib.mkEnableOption ''
        Wheter to enable production mode or fallback to dev mode
      '';

      useSocket = lib.mkOption {
        type = lib.types.bool;
        default = cfg.production;
        description = ''
          Whether to bind a unix socket instead of a TCP port.
          Defaults to the value of the production option.
        '';
      };

      domainName = lib.mkOption {
        type = lib.types.str;
        description = ''
          Domain name for the service
        '';
      };

      logLevel = lib.mkOption {
        type = lib.types.str;
        default = "WARN";
        description = ''
          Log level for the service
        '';
      };

      domainNameAliases = lib.mkOption {
        type = lib.types.listOf lib.types.str;
        description = ''
          List of alias domain names to be used
        '';
      };

      httpAddress = lib.mkOption {
        type = lib.types.str;
        default = "localhost";
        description = ''
          HTTP address for the ProcessIntel service
        '';
      };

      httpPort = lib.mkOption {
        type = lib.types.port;
        default = 8501;
        description = ''
          HTTP port for the ProcessIntel service
        '';
      };

      maxUploadSizeMb = lib.mkOption {
        type = lib.types.int;
        default = 200;
        description = ''
          Max Upload size for the ProcessIntel service in MB
        '';
      };

      tmpFileMaxAgeMinutes = lib.mkOption {
        type = lib.types.ints.positive;
        default = 60;
        description = ''
          Maximum age (in minutes) of temporary files.
          Files older than this are automatically removed.
        '';
      };

    };
  };

  config = lib.mkIf cfg.enable {

    systemd.services.${serviceName} = {
      description = "ProcessIntel service";
      before = [ "nginx.service" ];
      wantedBy = [ "multi-user.target" ];

      path = with pkgs; [
        coreutils
        findutils
        package
      ];

      environment = {
        FONTCONFIG_FILE = fontconfigFile;

        PROCESSINTEL_DOCS_DIR = "${package}/docs";
        PROCESSINTEL_TMP_DIR = "${cacheDir}/tmp";
        PROCESSINTEL_ASSETS_DIR = "${package}/assets";
        PROCESSINTEL_LOG_LEVEL = cfg.logLevel;

        STREAMLIT_SERVER_MAX_UPLOAD_SIZE = toString cfg.maxUploadSizeMb;
        STREAMLIT_SERVER_ENABLE_CORS = "true";
        STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION = "true";
        STREAMLIT_SERVER_HEADLESS = "true";
        STREAMLIT_BROWSER_GATHER_USAGE_STATS = "false";
        STREAMLIT_SERVER_FILE_WATCHER_TYPE = "none";
        STREAMLIT_CLIENT_TOOLBAR_MODE = "minimal";
      };

      script =
        if cfg.useSocket then
          ''
            processintel --socket ${socketFile}
          ''
        else
          ''
            processintel --host ${cfg.httpAddress} --port ${toString cfg.httpPort}
          '';

      serviceConfig = {
        DynamicUser = true;

        CacheDirectory = [ serviceName ];
        RuntimeDirectory = serviceName;
        RuntimeDirectoryMode = 750;
        WorkingDirectory = runtimeDir;

        MemoryDenyWriteExecute = true;
        PrivateDevices = true;
        PrivateNetwork = true;
        PrivateTmp = true;
        ProtectSystem = "full";
        ProtectHome = true;
        ProtectProc = "invisible";
        RestrictAddressFamilies = "AF_UNIX";

        ExecStartPost = lib.optional cfg.useSocket (
          let
            script = pkgs.writeShellScript "${serviceName}-start-post" ''
              remainingRetries=10
              while true; do
                echo "Testing socket existance, remaining retries: $remainingRetries"

                if [ "$remainingRetries" = 0 ]; then
                  echo "<3>Socket file not available after retry count was reached '${socketFile}'"
                  exit 1
                fi

                if [ -S "${socketFile}" ]; then
                  break
                fi

                sleep 1
                remainingRetries=$((remainingRetries-1))
              done

              chown :nginx "${runtimeDir}"
              chown :nginx "${socketFile}"
              chmod 660 "${socketFile}"
              echo "Service ready"
            '';
          in
          "+${script}"
        );

      };
    };

    systemd.services."${serviceName}-tmp-cleanup" = {
      description = "Cleanup tmp files for ProcessIntel service";
      startAt = "hourly";

      script = ''
        echo "Deleting tmp files in: $d"
        ${pkgs.findutils}/bin/find "${cacheDir}/tmp" \
          -type f \
          -mmin +${toString cfg.tmpFileMaxAgeMinutes} \
          -delete
      '';

      serviceConfig = {
        Type = "oneshot";
      };
    };

    services.nginx.upstreams.${serviceName} =
      if cfg.useSocket then
        {
          servers."unix:${socketFile}" = { };
          extraConfig = "keepalive 32;";
        }
      else
        {
          servers."${cfg.httpAddress}:${toString cfg.httpPort}" = { };
          extraConfig = "keepalive 32;";
        };

    # "https://discuss.streamlit.io/t/streamlit-docker-nginx-ssl-https/2195/3"
    # "https://discuss.streamlit.io/t/accessing-streamlit-through-reverse-proxy-results-in-please-wait-solved/8618"
    services.nginx.virtualHosts."${cfg.domainName}" = {
      enableACME = cfg.production;
      forceSSL = cfg.production;
      serverAliases = cfg.domainNameAliases;

      extraConfig = ''
        access_log /var/log/nginx/${cfg.domainName}.access.log json_analytics;
        error_log /var/log/nginx/${cfg.domainName}.error.log;
      '';

      locations."/" = {
        proxyPass = "http://${serviceName}/";
        proxyWebsockets = true;
        recommendedProxySettings = true;
        extraConfig = ''
          client_max_body_size ${toString cfg.maxUploadSizeMb}m;
        '';
      };

      locations."/stream" = {
        proxyPass = "http://${serviceName}/stream";
        proxyWebsockets = true;
        recommendedProxySettings = true;
      };

    };

  };
}
