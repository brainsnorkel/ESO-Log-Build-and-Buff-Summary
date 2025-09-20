# GraphQL queries for ESO Logs API

# GraphQL query to get report information including fights
GET_REPORT_BY_CODE_QUERY = """
query GetReportByCode($code: String!) {
  reportData {
    report(code: $code) {
      code
      title
      startTime
      endTime
      zone {
        id
        name
      }
      fights {
        id
        name
        startTime
        endTime
        difficulty
        kill
        bossPercentage
        fightPercentage
        maps {
          id
        }
      }
    }
  }
}
"""

# GraphQL query to get table data for a specific fight
GET_REPORT_TABLE_QUERY = """
query GetReportTable(
  $code: String!
  $startTime: Float
  $endTime: Float
  $dataType: TableDataType!
  $hostilityType: HostilityType
  $fightIDs: [Int]
) {
  reportData {
    report(code: $code) {
      table(
        startTime: $startTime
        endTime: $endTime
        dataType: $dataType
        hostilityType: $hostilityType
        fightIDs: $fightIDs
      )
    }
  }
}
"""

# GraphQL query to get available zones
GET_ZONES_QUERY = """
query GetZones {
  worldData {
    zones {
      id
      name
      encounters {
        id
        name
      }
    }
  }
}
"""

# GraphQL query to get top rankings for a specific zone/encounter
GET_RANKINGS_QUERY = """
query GetRankings(
  $zoneID: Int!
  $encounterID: Int
  $difficulty: Int
  $size: Int
  $page: Int
  $limit: Int
) {
  worldData {
    encounter(id: $encounterID) {
      characterRankings(
        zoneID: $zoneID
        difficulty: $difficulty
        size: $size
        page: $page
        limit: $limit
        metric: dps
      ) {
        data {
          name
          class
          spec
          amount
          report {
            code
            startTime
          }
          guild {
            name
          }
        }
        total
        per_page
        current_page
        has_more_pages
      }
    }
  }
}
"""

# GraphQL query to get reports for a specific zone
GET_REPORTS_QUERY = """
query GetReports(
  $zoneID: Int
  $page: Int
  $limit: Int
) {
  reportData {
    reports(
      zoneID: $zoneID
      page: $page
      limit: $limit
    ) {
      data {
        code
        title
        startTime
        endTime
        zone {
          id
          name
        }
        guild {
          id
          name
        }
        owner {
          name
        }
      }
      total
      per_page
      current_page
      has_more_pages
    }
  }
}
"""

# GraphQL query to get player abilities/casts for a specific fight
GET_PLAYER_ABILITIES_QUERY = """
query GetPlayerAbilities($code: String!, $startTime: Float!, $endTime: Float!) {
  reportData {
    report(code: $code) {
      table(
        dataType: Casts
        hostilityType: Friendlies
        startTime: $startTime
        endTime: $endTime
      ) {
        data {
          entries {
            name
            id
            guid
            type
            abilityGameID
            total
            activeTime
          }
          playerDetails {
            name
            id
            guid
            type
            displayName
          }
        }
      }
    }
  }
}
"""

# GraphQL query to get game abilities for ability name resolution
GET_GAME_ABILITIES_QUERY = """
query GetGameAbilities($limit: Int!, $page: Int!) {
  gameData {
    abilities(limit: $limit, page: $page) {
      data {
        id
        name
        icon
      }
      total
      per_page
      current_page
      has_more_pages
    }
  }
}
"""

# GraphQL query to get master data including all abilities used in the report
GET_REPORT_MASTER_DATA_QUERY = """
query GetReportMasterData($code: String!) {
  reportData {
    report(code: $code) {
      masterData {
        abilities {
          gameID
          name
          icon
          type
        }
        actors(type: "Player") {
          name
          id
          gameID
          type
          subType
        }
      }
    }
  }
}
"""

# GraphQL query to get buff/debuff uptime data for a fight
GET_BUFF_DEBUFF_UPTIMES_QUERY = """
query GetBuffDebuffUptimes($code: String!, $startTime: Float!, $endTime: Float!) {
  reportData {
    report(code: $code) {
      table(
        dataType: Buffs
        hostilityType: Friendlies
        startTime: $startTime
        endTime: $endTime
      ) {
        data {
          auras {
            name
            id
            guid
            totalUptime
            totalUses
          }
          totalTime
        }
      }
    }
  }
}
"""