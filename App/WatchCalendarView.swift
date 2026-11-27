import SwiftUI
import TVCore

/// 追剧日历: the followed series' episodes on a month grid, the day picked under it. Opened from Discover's toolbar.
struct WatchCalendarView: View {
    @Environment(Store.self) private var store
    @State private var schedules: [Int: AirSchedule] = [:]
    @State private var loading = false
    @State private var month = Date()
    @State private var picked: String?

    private var shows: [FollowedShow] { store.followedShows.shows }
    private var today: String { DiscoverFollowing.today }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                header
                if shows.isEmpty {
                    empty
                } else {
                    weekdayRow
                    grid
                    daySection
                }
            }
            .padding(.horizontal, 16)
            .padding(.bottom, 40)
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .background(ColorThemes.shared.current.palette.canvas)
        .navigationTitle(L10n.text("Following Calendar"))
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
        .task(id: shows.map(\.id)) { await load() }
    }

    // MARK: Pieces

    private var header: some View {
        HStack(spacing: 10) {
            Text(monthTitle).font(.system(size: 26, weight: .bold)).lineLimit(1)
            Spacer(minLength: 0)
            stepButton("chevron.left", by: -1)
            stepButton("chevron.right", by: 1)
        }
        .padding(.top, 10)
    }

    private func stepButton(_ symbol: String, by value: Int) -> some View {
        Button { step(value) } label: {
            Image(systemName: symbol)
                .font(.system(size: 14, weight: .semibold))
                .frame(width: 34, height: 34)
                .background(Color.primary.opacity(0.07), in: Circle())
        }
        .buttonStyle(.plain)
    }

    private var weekdayRow: some View {
        HStack(spacing: 6) {
            ForEach(0..<weekdaySymbols.count, id: \.self) { index in
                Text(weekdaySymbols[index])
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity)
            }
        }
    }

    private var grid: some View {
        LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 6), count: 7), spacing: 6) {
            ForEach(Array(0..<leading), id: \.self) { _ in
                Color.clear.frame(height: 46)
            }
            ForEach(days, id: \.self) { date in
                cell(date)
            }
        }
    }

    private func cell(_ date: Date) -> some View {
        let key = AirSchedule.day(date)
        let day = byDate[key]
        let isToday = key == today
        let isPicked = key == selectedDate
        return Button {
            picked = key
        } label: {
            VStack(spacing: 4) {
                Text("\(calendar.component(.day, from: date))")
                    .font(.system(size: 16, weight: isPicked ? .bold : .medium))
                    .foregroundStyle(isPicked ? Brand.onAccent : Color.primary)
                Circle()
                    .fill(day == nil ? Color.clear : Color.primary.opacity(isPicked ? 0.85 : 0.35))
                    .frame(width: 5, height: 5)
            }
            .frame(maxWidth: .infinity)
            .frame(height: 46)
            .background {
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .fill(isPicked ? Brand.accent : (isToday ? Brand.accent.opacity(0.14) : Color.clear))
            }
            .contentShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        }
        .buttonStyle(.plain)
    }

    @ViewBuilder private var daySection: some View {
        if let day = byDate[selectedDate] {
            VStack(alignment: .leading, spacing: 14) {
                Text("\(DiscoverFollowing.dayName(day.date, today: today)) · \(DiscoverFollowing.monthDay(day.date))")
                    .font(.system(size: 17, weight: .semibold))
                    .foregroundStyle(day.date == today ? AnyShapeStyle(Brand.accent) : AnyShapeStyle(.primary))
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(alignment: .top, spacing: 14) {
                        ForEach(day.entries) { entry in
                            RouteLink { DiscoverDetailView(item: entry.show.catalogItem) } label: {
                                card(entry)
                            }
                        }
                    }
                    .padding(.vertical, 2)
                }
            }
        } else if loading {
            ProgressView().frame(maxWidth: .infinity).padding(.vertical, 36)
        } else {
            Text(L10n.text("No upcoming episodes"))
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .padding(.vertical, 22)
        }
    }

    private func card(_ entry: AirSchedule.Upcoming) -> some View {
        VStack(alignment: .leading, spacing: 7) {
            AsyncImage(url: entry.show.poster) { phase in
                switch phase {
                case .success(let image): image.resizable().scaledToFill()
                default: Color.primary.opacity(0.08)
                }
            }
            .frame(width: 118, height: 168)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            Text(entry.show.name)
                .font(.system(size: 13, weight: .semibold))
                .lineLimit(2)
                .multilineTextAlignment(.leading)
                .frame(width: 118, alignment: .leading)
            Text(entry.day.map(DiscoverFollowing.episodes) ?? " ")
                .font(.system(size: 12))
                .foregroundStyle(.secondary)
                .lineLimit(1)
                .frame(width: 118, alignment: .leading)
        }
        .frame(width: 118, alignment: .leading)
        .contentShape(Rectangle())
    }

    private var empty: some View {
        VStack(spacing: 10) {
            Image(systemName: "calendar.badge.plus").font(.system(size: 36)).foregroundStyle(.secondary)
            Text(L10n.text("No Shows Followed")).font(.headline)
            Text(L10n.text("Open a series in Discover and tap Follow Show to see when its new episodes air."))
                .font(.footnote)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 60)
    }

    // MARK: Dates and data

    private var calendar: Calendar {
        var value = Calendar(identifier: .gregorian)
        value.timeZone = .current
        value.firstWeekday = 2
        return value
    }
    private var monthStart: Date {
        calendar.date(from: calendar.dateComponents([.year, .month], from: month)) ?? month
    }
    private var dayCount: Int { calendar.range(of: .day, in: .month, for: monthStart)?.count ?? 30 }
    private var days: [Date] { (0..<dayCount).compactMap { calendar.date(byAdding: .day, value: $0, to: monthStart) } }
    private var leading: Int { (calendar.component(.weekday, from: monthStart) - calendar.firstWeekday + 7) % 7 }

    private var monthTitle: String {
        monthStart.formatted(Date.FormatStyle(locale: Locale(identifier: L10n.resolvedLanguage())).year().month(.wide))
    }

    private var weekdaySymbols: [String] {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: L10n.resolvedLanguage())
        formatter.calendar = calendar
        let symbols = formatter.veryShortStandaloneWeekdaySymbols ?? []
        let start = calendar.firstWeekday - 1
        return (0..<7).compactMap { symbols.indices.contains(($0 + start) % 7) ? symbols[($0 + start) % 7] : nil }
    }

    private var agenda: [AirSchedule.AgendaDay] {
        AirSchedule.agenda(shows, schedules: schedules, today: today, from: AirSchedule.day(monthStart), days: dayCount)
    }
    private var byDate: [String: AirSchedule.AgendaDay] {
        agenda.reduce(into: [:]) { result, day in result[day.date] = day }
    }
    private var selectedDate: String {
        if let picked, byDate[picked] != nil { return picked }
        if byDate[today] != nil { return today }
        return byDate.keys.sorted().first ?? ""
    }

    private func step(_ value: Int) {
        guard let next = calendar.date(byAdding: .month, value: value, to: monthStart) else { return }
        month = next
        picked = nil
    }

    private func load() async {
        guard !shows.isEmpty else { schedules = [:]; return }
        loading = true
        let ids = shows.map(\.id)
        let kept = await AirSchedules.shared.cached(ids)
        if !Task.isCancelled, !kept.isEmpty { schedules.merge(kept) { _, new in new } }
        let fresh = await AirSchedules.shared.schedules(ids)
        if !Task.isCancelled { schedules.merge(fresh) { _, new in new } }
        loading = false
    }
}
